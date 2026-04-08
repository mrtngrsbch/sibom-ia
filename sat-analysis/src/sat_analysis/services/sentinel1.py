"""
Cliente de Microsoft Planetary Computer para Sentinel-1 SAR.

Permite buscar y procesar imágenes de radar de apertura sintética (SAR)
independientes de cobertura nubosa, para detección de agua y humedad.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import planetary_computer
import pystac_client
import rioxarray
from pyproj import CRS, Transformer

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class S1Image:
    """Metadatos de una imagen Sentinel-1."""

    item_id: str
    datetime: str
    bbox: list[float]
    platform: str  # 'sentinel-1a' or 'sentinel-1b'
    assets: dict[str, Any]


@dataclass(frozen=True)
class S1BandData:
    """Datos de bandas SAR descargadas."""

    vv: np.ndarray  # VV polarization (linear scale)
    vh: np.ndarray  # VH polarization (linear scale)
    transform: Any
    crs: Any


class Sentinel1Error(Exception):
    """Error al consultar/procesar datos Sentinel-1."""

    pass


class Sentinel1Service:
    """
    Cliente para imágenes Sentinel-1 SAR de Planetary Computer.

    Usa la colección `sentinel-1-rtc` (Radiometrically Terrain Corrected).
    Los valores están en escala lineal (no dB).

    Umbrales de detección de agua (escala lineal):
    - Agua:      VV < 0.05  (~-13 dB)
    - Agua:      VH < 0.02  (~-17 dB)
    - Suelo húmedo: 0.05 <= VV < 0.15
    - Vegetación: VV >= 0.15
    """

    COLLECTION = "sentinel-1-rtc"
    WATER_VV_THRESHOLD = 0.05
    WATER_VH_THRESHOLD = 0.02
    MOIST_VV_THRESHOLD = 0.15

    def __init__(
        self,
        stac_url: str = "https://planetarycomputer.microsoft.com/api/stac/v1",
    ) -> None:
        self.stac_url = stac_url
        self._catalog: pystac_client.Client | None = None

    def _get_catalog(self) -> pystac_client.Client:
        if self._catalog is None:
            self._catalog = pystac_client.Client.open(self.stac_url)
        return self._catalog

    def search_sampled(
        self,
        bbox: list[float],
        date_range: str,
        samples_per_year: int = 4,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[S1Image]:
        """
        Busca imágenes Sentinel-1 con muestreo temporal uniforme.

        SAR no requiere filtro de nubes.

        Args:
            bbox: [min_lon, min_lat, max_lon, max_lat]
            date_range: Rango de fechas formato "start/end"
            samples_per_year: Imágenes objetivo por año
            start_date: Fecha inicio (opcional)
            end_date: Fecha fin (opcional)

        Returns:
            Lista de S1Image ordenada de más reciente a más antigua

        Raises:
            Sentinel1Error: Si hay error en la búsqueda STAC
        """
        catalog = self._get_catalog()

        if end_date is None:
            end_date = datetime.now()
        if start_date is None and "/" in date_range:
            start_date = datetime.fromisoformat(date_range.split("/")[0])
        if start_date is None:
            raise Sentinel1Error("Se requiere start_date o date_range válido")

        total_days = (end_date - start_date).days
        if total_days <= 0:
            return []

        target_count = max(1, int(round(samples_per_year * (total_days / 365.25))))
        interval_days = total_days / target_count

        results: list[S1Image] = []
        for i in range(target_count):
            interval_start = start_date + timedelta(days=i * interval_days)
            interval_end = start_date + timedelta(days=(i + 1) * interval_days)
            interval_str = (
                f"{interval_start.strftime('%Y-%m-%d')}"
                f"/{interval_end.strftime('%Y-%m-%d')}"
            )

            try:
                search = catalog.search(
                    collections=[self.COLLECTION],
                    bbox=bbox,
                    datetime=interval_str,
                    max_items=20,
                )
                items = list(search.items())
                if not items:
                    continue

                # Sin filtro de nubes — elegir el primero disponible
                best = items[0]
                results.append(
                    S1Image(
                        item_id=best.id,
                        datetime=best.properties["datetime"],
                        bbox=best.bbox,
                        platform=best.properties.get("platform", "sentinel-1"),
                        assets={k: v.to_dict() for k, v in best.assets.items()},
                    )
                )
            except Exception as exc:
                logger.debug("Sentinel-1 intervalo %s sin imágenes: %s", interval_str, exc)
                continue

        results.sort(key=lambda x: x.datetime, reverse=True)
        return results

    def download_bands(
        self,
        item: S1Image,
        bbox: list[float] | None = None,
    ) -> S1BandData:
        """
        Descarga bandas VV y VH de una imagen Sentinel-1.

        Args:
            item: S1Image con metadatos
            bbox: Área de interés en WGS84

        Returns:
            S1BandData con VV y VH en escala lineal

        Raises:
            Sentinel1Error: Si no se puede descargar
        """
        catalog = self._get_catalog()

        search = catalog.search(collections=[self.COLLECTION], ids=[item.item_id])
        items = list(search.items())
        if not items:
            raise Sentinel1Error(f"No se encontró item Sentinel-1: {item.item_id}")

        signed = planetary_computer.sign(items[0])

        # Expandir bbox con margen
        clip_bbox = bbox
        if bbox is not None:
            lon_w = bbox[2] - bbox[0]
            lat_h = bbox[3] - bbox[1]
            margin = 0.30
            clip_bbox = [
                bbox[0] - lon_w * margin,
                bbox[1] - lat_h * margin,
                bbox[2] + lon_w * margin,
                bbox[3] + lat_h * margin,
            ]

        try:
            vv_href = signed.assets["vv"].href
        except KeyError:
            raise Sentinel1Error("No se encontró banda VV en la imagen Sentinel-1")

        vv_ds = rioxarray.open_rasterio(vv_href, masked=True)
        image_crs = vv_ds.rio.crs

        utm_bbox = self._convert_bbox_to_crs(clip_bbox, image_crs)

        if utm_bbox is not None:
            vv_ds = vv_ds.rio.clip_box(
                minx=utm_bbox[0],
                miny=utm_bbox[1],
                maxx=utm_bbox[2],
                maxy=utm_bbox[3],
            )

        vv_data = np.array(vv_ds.values[0], dtype=np.float32)
        transform = vv_ds.rio.transform()
        crs = vv_ds.rio.crs
        vv_ds.close()

        # Descargar VH (opcional)
        vh_data = np.zeros_like(vv_data)
        if "vh" in signed.assets:
            try:
                vh_href = signed.assets["vh"].href
                vh_ds = rioxarray.open_rasterio(vh_href, masked=True)
                if utm_bbox is not None:
                    try:
                        vh_ds = vh_ds.rio.clip_box(
                            minx=utm_bbox[0],
                            miny=utm_bbox[1],
                            maxx=utm_bbox[2],
                            maxy=utm_bbox[3],
                        )
                    except Exception:
                        pass
                vh_raw = np.array(vh_ds.values[0], dtype=np.float32)
                vh_ds.close()

                # Remuestrear al shape de VV si difieren
                if vh_raw.shape != vv_data.shape:
                    from scipy.ndimage import zoom  # type: ignore[import-untyped]
                    zy = vv_data.shape[0] / vh_raw.shape[0]
                    zx = vv_data.shape[1] / vh_raw.shape[1]
                    vh_data = zoom(vh_raw, [zy, zx], order=1).astype(np.float32)
                else:
                    vh_data = vh_raw
            except Exception as exc:
                logger.warning("No se pudo descargar VH: %s", exc)

        return S1BandData(vv=vv_data, vh=vh_data, transform=transform, crs=crs)

    def compute_water_areas(
        self, bands: S1BandData, pixel_area_m2: float
    ) -> dict[str, float]:
        """
        Calcula áreas de agua y suelo húmedo usando umbrales SAR.

        Args:
            bands: Datos SAR descargados
            pixel_area_m2: Área por píxel en m²

        Returns:
            dict con water_ha, moist_ha, dry_ha, total_ha
        """
        valid = np.isfinite(bands.vv) & (bands.vv > 0)
        water_mask = valid & (bands.vv < self.WATER_VV_THRESHOLD)
        moist_mask = valid & ~water_mask & (bands.vv < self.MOIST_VV_THRESHOLD)
        dry_mask = valid & (bands.vv >= self.MOIST_VV_THRESHOLD)

        def _ha(mask: np.ndarray) -> float:
            return round(float(np.sum(mask) * pixel_area_m2 / 10000), 2)

        return {
            "water_ha": _ha(water_mask),
            "moist_ha": _ha(moist_mask),
            "dry_ha": _ha(dry_mask),
            "total_ha": _ha(valid),
        }

    @staticmethod
    def _convert_bbox_to_crs(
        bbox: list[float] | None,
        target_crs: Any,
    ) -> list[float] | None:
        """Convierte un bbox WGS84 al CRS de la imagen."""
        if bbox is None or target_crs is None:
            return bbox
        try:
            src = CRS.from_epsg(4326)
            dst = CRS.from_user_input(target_crs)
            if src == dst:
                return bbox
            transformer = Transformer.from_crs(src, dst, always_xy=True)
            min_x, min_y = transformer.transform(bbox[0], bbox[1])
            max_x, max_y = transformer.transform(bbox[2], bbox[3])
            return [min_x, min_y, max_x, max_y]
        except Exception:
            return bbox
