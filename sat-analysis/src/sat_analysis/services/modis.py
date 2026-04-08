"""
Cliente de Microsoft Planetary Computer para MODIS.

Proporciona datos de resolución media (500 m) con alta frecuencia temporal
(composites de 8 días) para monitoreo de vegetación e índices hídricos.

Colección: modis-09A1-061 (MOD09A1 - Terra Surface Reflectance 8-Day 500m)
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
class ModisImage:
    """Metadatos de una imagen MODIS."""

    item_id: str
    datetime: str
    bbox: list[float]
    assets: dict[str, Any]


@dataclass(frozen=True)
class ModisBandData:
    """Datos de bandas MODIS descargadas (reflectancias superficiales 0-1)."""

    red: np.ndarray    # Band 1  620-670 nm
    nir: np.ndarray    # Band 2  841-876 nm
    blue: np.ndarray   # Band 3  459-479 nm
    green: np.ndarray  # Band 4  545-565 nm
    transform: Any
    crs: Any


class ModisError(Exception):
    """Error al consultar/procesar datos MODIS."""

    pass


class ModisService:
    """
    Cliente para imágenes MODIS MOD09A1 de Planetary Computer.

    MOD09A1 es un composite de 8 días con corrección atmosférica
    a 500 m de resolución.

    Índices disponibles con estas bandas:
    - NDVI = (NIR - Red) / (NIR + Red)
    - NDWI = (Green - NIR) / (Green + NIR)
    - EVI  = 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)
    """

    COLLECTION = "modis-09A1-061"
    SCALE_FACTOR = 0.0001  # Factor de escala del producto MOD09A1

    # Mapeo nombre lógico → clave de asset en el catálogo
    BAND_ASSETS: dict[str, str] = {
        "red": "sur_refl_b01",
        "nir": "sur_refl_b02",
        "blue": "sur_refl_b03",
        "green": "sur_refl_b04",
    }

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
    ) -> list[ModisImage]:
        """
        Busca imágenes MODIS con muestreo temporal uniforme.

        Args:
            bbox: [min_lon, min_lat, max_lon, max_lat]
            date_range: Rango de fechas formato "start/end"
            samples_per_year: Imágenes objetivo por año
            start_date: Fecha inicio (opcional)
            end_date: Fecha fin (opcional)

        Returns:
            Lista de ModisImage ordenada de más reciente a más antigua

        Raises:
            ModisError: Si hay error en la búsqueda STAC
        """
        catalog = self._get_catalog()

        if end_date is None:
            end_date = datetime.now()
        if start_date is None and "/" in date_range:
            start_date = datetime.fromisoformat(date_range.split("/")[0])
        if start_date is None:
            raise ModisError("Se requiere start_date o date_range válido")

        total_days = (end_date - start_date).days
        if total_days <= 0:
            return []

        target_count = max(1, int(round(samples_per_year * (total_days / 365.25))))
        interval_days = total_days / target_count

        results: list[ModisImage] = []
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
                    max_items=10,
                )
                items = list(search.items())
                if not items:
                    continue

                best = items[0]
                # Algunos items STAC de MODIS tienen datetime=None y usan
                # start_datetime/end_datetime en su lugar.
                dt = (
                    best.properties.get("datetime")
                    or best.properties.get("start_datetime")
                    or best.properties.get("end_datetime")
                    or interval_str.split("/")[0]
                )
                results.append(
                    ModisImage(
                        item_id=best.id,
                        datetime=dt,
                        bbox=best.bbox,
                        assets={k: v.to_dict() for k, v in best.assets.items()},
                    )
                )
            except Exception as exc:
                logger.debug("MODIS intervalo %s sin imágenes: %s", interval_str, exc)
                continue

        results.sort(key=lambda x: x.datetime or "", reverse=True)
        return results

    def download_bands(
        self,
        item: ModisImage,
        bbox: list[float] | None = None,
    ) -> ModisBandData:
        """
        Descarga las 4 bandas espectrales de MODIS MOD09A1.

        Args:
            item: ModisImage con metadatos
            bbox: Área de interés en WGS84

        Returns:
            ModisBandData con reflectancias superficiales escaladas (0–1)

        Raises:
            ModisError: Si no se puede descargar
        """
        catalog = self._get_catalog()

        search = catalog.search(collections=[self.COLLECTION], ids=[item.item_id])
        items = list(search.items())
        if not items:
            raise ModisError(f"No se encontró item MODIS: {item.item_id}")

        signed = planetary_computer.sign(items[0])

        # Añadir margen mayor dado el tamaño de píxel de 500 m
        clip_bbox_wgs84 = bbox
        if bbox is not None:
            lon_w = bbox[2] - bbox[0]
            lat_h = bbox[3] - bbox[1]
            margin = 0.50
            clip_bbox_wgs84 = [
                bbox[0] - lon_w * margin,
                bbox[1] - lat_h * margin,
                bbox[2] + lon_w * margin,
                bbox[3] + lat_h * margin,
            ]

        # Descargar todas las bandas
        band_arrays: dict[str, np.ndarray] = {}
        transform_out: Any = None
        crs_out: Any = None
        utm_bbox: list[float] | None = None

        for band_name, asset_key in self.BAND_ASSETS.items():
            if asset_key not in signed.assets:
                logger.warning("Band %s (%s) no disponible en item %s", band_name, asset_key, item.item_id)
                continue

            href = signed.assets[asset_key].href
            try:
                ds = rioxarray.open_rasterio(href, masked=True)
            except Exception as exc:
                logger.warning("Error abriendo banda %s: %s", band_name, exc)
                continue

            # Calcular utm_bbox la primera vez
            if utm_bbox is None and clip_bbox_wgs84 is not None:
                utm_bbox = self._convert_bbox_to_crs(clip_bbox_wgs84, ds.rio.crs)

            if utm_bbox is not None:
                try:
                    ds = ds.rio.clip_box(
                        minx=utm_bbox[0],
                        miny=utm_bbox[1],
                        maxx=utm_bbox[2],
                        maxy=utm_bbox[3],
                    )
                except Exception as exc:
                    logger.debug("clip_box sin efecto en %s: %s", band_name, exc)

            raw = np.array(ds.values[0], dtype=np.float32)
            # Aplicar factor de escala y clip a rango válido
            scaled = np.clip(raw * self.SCALE_FACTOR, -1.0, 1.0)

            if transform_out is None:
                transform_out = ds.rio.transform()
                crs_out = ds.rio.crs

            band_arrays[band_name] = scaled
            ds.close()

        if not band_arrays:
            raise ModisError(f"No se pudieron descargar bandas del item {item.item_id}")

        # Usar red como referencia de shape; si falta, crear arrays vacíos
        ref_shape = next(iter(band_arrays.values())).shape
        for band_name in ("red", "nir", "blue", "green"):
            if band_name not in band_arrays:
                band_arrays[band_name] = np.zeros(ref_shape, dtype=np.float32)

        # Alinear shapes con interpolación bilineal
        ref_shape = band_arrays["red"].shape
        for band_name in ("nir", "blue", "green"):
            arr = band_arrays[band_name]
            if arr.shape != ref_shape:
                from scipy.ndimage import zoom  # type: ignore[import-untyped]
                zy = ref_shape[0] / arr.shape[0]
                zx = ref_shape[1] / arr.shape[1]
                band_arrays[band_name] = zoom(arr, [zy, zx], order=1).astype(np.float32)

        return ModisBandData(
            red=band_arrays["red"],
            nir=band_arrays["nir"],
            blue=band_arrays["blue"],
            green=band_arrays["green"],
            transform=transform_out,
            crs=crs_out,
        )

    @staticmethod
    def compute_indices(bands: ModisBandData) -> dict[str, np.ndarray]:
        """
        Calcula índices espectrales a partir de las bandas MODIS.

        Returns:
            dict con claves: ndvi, ndwi, evi
            Todos los valores en rango [-1, 1] aproximadamente.
        """
        eps = 1e-6

        # NDVI = (NIR - Red) / (NIR + Red)
        ndvi_num = bands.nir - bands.red
        ndvi_den = bands.nir + bands.red + eps
        ndvi = np.where(ndvi_den > eps, ndvi_num / ndvi_den, 0.0).astype(np.float32)

        # NDWI = (Green - NIR) / (Green + NIR)
        ndwi_num = bands.green - bands.nir
        ndwi_den = bands.green + bands.nir + eps
        ndwi = np.where(ndwi_den > eps, ndwi_num / ndwi_den, 0.0).astype(np.float32)

        # EVI = 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)
        evi_num = 2.5 * (bands.nir - bands.red)
        evi_den = (bands.nir + 6.0 * bands.red - 7.5 * bands.blue + 1.0) + eps
        evi = np.where(np.abs(evi_den) > eps, evi_num / evi_den, 0.0).astype(np.float32)
        evi = np.clip(evi, -1.0, 1.0)

        return {"ndvi": ndvi, "ndwi": ndwi, "evi": evi}

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
