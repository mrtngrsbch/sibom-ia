"""
Cliente del servicio STAC de Microsoft Planetary Computer.

Permite buscar y descargar imágenes Sentinel-2 L2A para análisis
de índices espectrales.
"""
import pystac_client
import planetary_computer
import rioxarray
from datetime import date, datetime
from dataclasses import dataclass
from typing import Any
import numpy as np
from pyproj import Transformer, CRS
from shapely.geometry import shape


@dataclass(frozen=True)
class SatelliteImage:
    """Metadatos de una imagen satelital."""

    item_id: str
    datetime: str
    cloud_cover: float
    bbox: list[float]
    assets: dict[str, Any]


@dataclass(frozen=True)
class BandData:
    """Datos de bandas espectrales descargadas."""

    b02: np.ndarray  # Blue
    b03: np.ndarray  # Green
    b04: np.ndarray  # Red
    b08: np.ndarray  # NIR
    b11: np.ndarray  # SWIR1
    b12: np.ndarray  # SWIR2 (para detección de salinidad)
    transform: Any  # Transformación geoespacial
    crs: Any  # Sistema de referencia de coordenadas


class StacError(Exception):
    """Error al consultar el servicio STAC."""

    pass


class StacService:
    """
    Cliente del servicio STAC de Microsoft Planetary Computer.

    Proporciona métodos para buscar imágenes Sentinel-2 L2A
    y descargar las bandas espectrales necesarias para el cálculo
    de índices de agua, vegetación y humedad.
    """

    def __init__(
        self, stac_url: str = "https://planetarycomputer.microsoft.com/api/stac/v1"
    ):
        """
        Inicializa el cliente STAC.

        Args:
            stac_url: URL del catálogo STAC
        """
        self.stac_url = stac_url
        self.catalog: pystac_client.Client | None = None
        self.collection = "sentinel-2-l2a"

    def _get_catalog(self) -> pystac_client.Client:
        """Retorna el catálogo STAC (lazy initialization)."""
        if self.catalog is None:
            self.catalog = pystac_client.Client.open(self.stac_url)
        return self.catalog

    def search_sentinel(
        self,
        bbox: list[float],
        date_range: str,
        max_clouds: float = 20.0,
        limit: int = 100,
    ) -> list[SatelliteImage]:
        """
        Busca imágenes Sentinel-2 L2A por área y fecha.

        Args:
            bbox: [min_lon, min_lat, max_lon, max_lat]
            date_range: Rango de fechas en formato "start/end"
            max_clouds: Porcentaje máximo de cobertura de nubes
            limit: Máximo número de resultados

        Returns:
            Lista de SatelliteImage encontradas

        Raises:
            StacError: Si hay error en la búsqueda
        """
        catalog = self._get_catalog()

        try:
            search = catalog.search(
                collections=[self.collection],
                bbox=bbox,
                datetime=date_range,
                query={"eo:cloud_cover": {"lt": max_clouds}},
                max_items=limit,
            )

            items = list(search.items())

        except Exception as e:
            raise StacError(f"Error en búsqueda STAC: {e}")

        if not items:
            return []

        # Convertir a SatelliteImage
        results = []
        for item in items:
            results.append(
                SatelliteImage(
                    item_id=item.id,
                    datetime=item.properties["datetime"],
                    cloud_cover=item.properties.get("eo:cloud_cover", 0),
                    bbox=item.bbox,
                    assets={k: v.to_dict() for k, v in item.assets.items()},
                )
            )

        return results

    def search_sentinel_sampled(
        self,
        bbox: list[float],
        date_range: str,
        max_clouds: float = 20.0,
        samples_per_year: int = 4,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[SatelliteImage]:
        """
        Busca imágenes con muestreo temporal uniforme.

        En lugar de retornar las imágenes más recientes, divide el período
        en intervalos uniformes y selecciona la mejor imagen de cada intervalo.

        Args:
            bbox: [min_lon, min_lat, max_lon, max_lat]
            date_range: Rango de fechas en formato "start/end"
            max_clouds: Porcentaje máximo de cobertura de nubes
            samples_per_year: Número de muestras por año (default: 4 trimestral)
            start_date: Fecha de inicio del período (datetime)
            end_date: Fecha de fin del período (datetime)

        Returns:
            Lista de SatelliteImage con distribución temporal uniforme

        Raises:
            StacError: Si hay error en la búsqueda

        Ejemplo:
            Para 10 años con samples_per_year=4:
            - Busca todas las imágenes disponibles
            - Divide el período en 40 intervalos (4 por año)
            - Selecciona la mejor imagen de cada intervalo
            - Retorna ~40 imágenes distribuidas uniformemente
        """
        from datetime import timedelta

        catalog = self._get_catalog()

        # Calcular fecha inicio/fin si no se proporcionaron
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            # Parsear desde date_range
            if "/" in date_range:
                start_str = date_range.split("/")[0]
                start_date = datetime.fromisoformat(start_str)

        # Calcular total de muestras objetivo
        total_days = (end_date - start_date).days
        target_count = samples_per_year * (total_days / 365.25)
        target_count = int(round(target_count))

        if target_count <= 0:
            target_count = 1

        # Crear intervalos de tiempo
        interval_days = total_days / target_count
        intervals = []
        for i in range(target_count):
            interval_start = start_date + timedelta(days=i * interval_days)
            interval_end = start_date + timedelta(days=(i + 1) * interval_days)
            intervals.append((interval_start, interval_end))

        console = None
        try:
            from rich.console import Console
            console = Console()
        except ImportError:
            pass

        # Buscar la mejor imagen en cada intervalo
        results = []

        for i, (interval_start, interval_end) in enumerate(intervals):
            interval_str = f"{interval_start.strftime('%Y-%m-%d')}/{interval_end.strftime('%Y-%m-%d')}"

            try:
                # Buscar imágenes en este intervalo (sin límite estricto)
                search = catalog.search(
                    collections=[self.collection],
                    bbox=bbox,
                    datetime=interval_str,
                    query={"eo:cloud_cover": {"lt": max_clouds}},
                    max_items=50,  # Buscar hasta 50 por intervalo
                )

                items = list(search.items())

                if not items:
                    continue  # No hay imágenes en este intervalo

                # Filtrar imágenes que cubren completamente el BBOX de la parcela
                # Esto es necesario porque las parcelas cerca del borde de un tile
                # de Sentinel-2 pueden quedar recortadas
                items_fully_covering = []
                for item in items:
                    item_bbox = item.bbox  # [min_lon, min_lat, max_lon, max_lat]
                    # Verificar que el tile cubre completamente nuestro BBOX
                    fully_covers = (
                        item_bbox[0] <= bbox[0] and  # min_lon
                        item_bbox[1] <= bbox[1] and  # min_lat
                        item_bbox[2] >= bbox[2] and  # max_lon
                        item_bbox[3] >= bbox[3]      # max_lat
                    )
                    if fully_covers:
                        items_fully_covering.append(item)

                # Si ninguna imagen cubre completamente, usar la mejor de las disponibles
                # (pero esto puede causar recortes en la parcela)
                if not items_fully_covering:
                    items_fully_covering = items

                # Seleccionar la imagen con menos nubes del intervalo
                best_item = min(items_fully_covering, key=lambda x: x.properties.get("eo:cloud_cover", 100))

                results.append(
                    SatelliteImage(
                        item_id=best_item.id,
                        datetime=best_item.properties["datetime"],
                        cloud_cover=best_item.properties.get("eo:cloud_cover", 0),
                        bbox=best_item.bbox,
                        assets={k: v.to_dict() for k, v in best_item.assets.items()},
                    )
                )

            except Exception as e:
                # Continuar con el siguiente intervalo si hay error
                if console:
                    console.print(f"[dim]   Intervalo {i+1}/{len(intervals)}: sin imágenes[/dim]")
                continue

        # Ordenar por fecha descendente (más reciente primero)
        results.sort(key=lambda x: x.datetime, reverse=True)

        return results

    def search_multi_collection(
        self,
        bbox: list[float],
        date_range: str,
        max_clouds: float = 20.0,
        limit: int = 100,
        collections: list[str] | None = None,
    ) -> list[SatelliteImage]:
        """
        Busca imágenes en múltiples colecciones STAC y combina resultados.

        Útil para aumentar la frecuencia de imágenes combinando Sentinel-2
        con HLS (Harmonized Landsat-Sentinel-2).

        Args:
            bbox: [min_lon, min_lat, max_lon, max_lat]
            date_range: Rango de fechas en formato "start/end"
            max_clouds: Porcentaje máximo de cobertura de nubes
            limit: Máximo número de resultados por colección
            collections: Lista de colecciones (default: S2 + HLS)

        Returns:
            Lista de SatelliteImage encontradas, ordenadas por fecha (más reciente primero)

        Raises:
            StacError: Si hay error en la búsqueda

        Nota:
            Colecciones HLS disponibles:
            - HLS.S30: Sentinel-30m (harmonized de Sentinel-2)
            - HLS.L30: Landsat-30m (harmonized de Landsat 8)
        """
        if collections is None:
            # Por defecto: Sentinel-2 + HLS (S30 y L30)
            collections = ["sentinel-2-l2a", "HLS.S30", "HLS.L30"]

        catalog = self._get_catalog()
        all_items = []

        for collection in collections:
            try:
                search = catalog.search(
                    collections=[collection],
                    bbox=bbox,
                    datetime=date_range,
                    query={"eo:cloud_cover": {"lt": max_clouds}},
                    max_items=limit,
                )

                items = list(search.items())

                # Convertir a SatelliteImage con metadata de colección
                for item in items:
                    all_items.append(
                        SatelliteImage(
                            item_id=item.id,
                            datetime=item.properties["datetime"],
                            cloud_cover=item.properties.get("eo:cloud_cover", 0),
                            bbox=item.bbox,
                            assets={k: v.to_dict() for k, v in item.assets.items()},
                        )
                    )

            except Exception as e:
                # No fallar si una colección no responde, continuar con las demás
                import warnings
                warnings.warn(f"Error buscando colección {collection}: {e}")

        # Ordenar por fecha (más reciente primero)
        all_items.sort(key=lambda x: x.datetime, reverse=True)

        return all_items

    def download_bands(
        self,
        item: SatelliteImage,
        bbox: list[float] | None = None,
        geometry: dict | None = None,
    ) -> BandData:
        """
        Descarga las bandas espectrales necesarias.

        Args:
            item: SatelliteImage con metadatos
            bbox: Área de interés [min_lon, min_lat, max_lon, max_lat]
                   Si es None, descarga toda la escena
            geometry: GeoJSON geometría para clip preciso (opcional)

        Returns:
            BandData con las bandas B02, B03, B04, B08, B11, B12 (todas a 10m)

        Raises:
            StacError: Si hay error en la descarga

        Nota:
            B11 y B12 tienen resolución 20m, se remuestrean a 10m para coincidir
            con las otras bandas. B12 se usa para detección de salinización.
        """
        catalog = self._get_catalog()

        # Buscar el item original para hacer signing
        search = catalog.search(collections=[self.collection], ids=[item.item_id])
        items = list(search.items())

        if not items:
            raise StacError(f"No se encontró item {item.item_id}")

        stac_item = items[0]

        # Firmar URLs (SAS token para Azure Blob Storage)
        signed_item = planetary_computer.sign(stac_item)

        # Bandas que necesitamos (B11 y B12 son 20m, las otras son 10m)
        band_names = ["B02", "B03", "B04", "B08", "B11", "B12"]

        try:
            # Descargar con rioxarray
            datasets = {}

            # Abrir la primera banda para detectar el CRS de la imagen
            first_asset = signed_item.assets[band_names[0]]
            first_href = first_asset.href
            first_ds = rioxarray.open_rasterio(first_href, masked=True)
            image_crs = first_ds.rio.crs

            # Agregar margen de seguridad al BBOX para evitar recortar la parcela
            # Esto asegura que toda la geometría esté dentro de la imagen descargada
            # El margen debe ser generoso porque la conversión de coordenadas y
            # el alineamiento de la grilla de píxeles pueden causar recortes
            clip_bbox = bbox
            if bbox is not None:
                # Margen del 30% para asegurar que la parcela completa esté en la imagen
                # Esto compensa errores de conversión CRS y alineación de píxeles
                margin = 0.30  # 30%
                lon_width = bbox[2] - bbox[0]
                lat_height = bbox[3] - bbox[1]

                lon_margin = lon_width * margin
                lat_margin = lat_height * margin

                clip_bbox = [
                    bbox[0] - lon_margin,  # min_lon
                    bbox[1] - lat_margin,  # min_lat
                    bbox[2] + lon_margin,  # max_lon
                    bbox[3] + lat_margin,  # max_lat
                ]

            # Convertir bbox de WGS84 a UTM si es necesario
            utm_bbox = clip_bbox
            if clip_bbox is not None and image_crs is not None:
                # El bbox está en WGS84, convertir al CRS de la imagen (UTM)
                bbox_crs = CRS.from_epsg(4326)  # WGS84
                image_crs_obj = CRS.from_user_input(image_crs)

                if bbox_crs != image_crs_obj:
                    # Crear transformador
                    transformer = Transformer.from_crs(
                        bbox_crs, image_crs_obj, always_xy=True
                    )
                    # IMPORTANTE: Usar clip_bbox (con margen) NO bbox original
                    # Transformar las 4 esquinas del bbox expandido
                    min_x, min_y = transformer.transform(clip_bbox[0], clip_bbox[1])
                    max_x, max_y = transformer.transform(clip_bbox[2], clip_bbox[3])
                    utm_bbox = [min_x, min_y, max_x, max_y]

            # Cerrar el primer dataset
            first_ds.close()

            # Preparar geometría para clip si se proporcionó
            clip_geometry = None
            if geometry is not None:
                # La geometría viene en EPSG:4326 (WGS84)
                # Necesitamos convertirla al CRS de la imagen (UTM)
                geom_crs = CRS.from_epsg(4326)
                image_crs_obj = CRS.from_user_input(image_crs)

                if geom_crs != image_crs_obj:
                    # Crear transformador
                    transformer = Transformer.from_crs(
                        geom_crs, image_crs_obj, always_xy=True
                    )
                    # Transformar geometría
                    from shapely.ops import transform
                    clip_geometry = transform(transformer.transform, shape(geometry))
                else:
                    clip_geometry = shape(geometry)

            # Descargar todas las bandas
            for band in band_names:
                asset = signed_item.assets[band]
                href = asset.href

                # Abrir con rioxarray (sin chunks para leer inmediatamente el bbox)
                ds = rioxarray.open_rasterio(href, masked=True)

                # Primero recortar al bbox en UTM para reducir área
                if utm_bbox is not None:
                    ds = ds.rio.clip_box(
                        minx=utm_bbox[0],
                        miny=utm_bbox[1],
                        maxx=utm_bbox[2],
                        maxy=utm_bbox[3],
                    )

                # Luego clip por geometría si está disponible
                if clip_geometry is not None:
                    ds = ds.rio.clip([clip_geometry], ds.rio.crs)

                datasets[band] = ds

            # B11 y B12 tienen resolución 20m, necesitamos remuestrear a 10m
            # Obtenemos el shape objetivo de B02 (10m)
            target_shape = datasets["B02"].shape[1:]  # (height, width)

            # Función helper para remuestrear bandas de 20m a 10m
            def resample_to_10m(band_ds: "xr.DataArray", target_shape: tuple[int, int]) -> "xr.DataArray":
                """Remuestrea una banda de 20m a 10m usando interpolación bilineal."""
                from scipy import ndimage
                import xarray as xr

                # Obtener datos y remuestrear
                data_20m = band_ds.values[0]
                # Usar zoom para remuestrear de 20m a 10m (factor 2)
                data_10m = ndimage.zoom(data_20m, 2, order=1)

                # Recortar o hacer padding para match exacto
                h, w = data_10m.shape
                target_h, target_w = target_shape

                if h > target_h:
                    data_10m = data_10m[:target_h, :]
                elif h < target_h:
                    pad_h = target_h - h
                    data_10m = np.pad(data_10m, ((0, pad_h), (0, 0)), mode='edge')

                if w > target_w:
                    data_10m = data_10m[:, :target_w]
                elif w < target_w:
                    pad_w = target_w - w
                    data_10m = np.pad(data_10m, ((0, 0), (0, pad_w)), mode='edge')

                # Crear nuevo DataArray con shape correcto
                return xr.DataArray(
                    data_10m[np.newaxis, :, :],
                    dims=("band", "y", "x"),
                    coords={
                        "band": [1],
                        "y": datasets["B02"].y,
                        "x": datasets["B02"].x,
                    }
                )

            # Remuestrear B11 y B12 si es necesario
            b11_ds = datasets["B11"]
            if b11_ds.shape[1:] != target_shape:
                b11_ds = resample_to_10m(b11_ds, target_shape)

            b12_ds = datasets["B12"]
            if b12_ds.shape[1:] != target_shape:
                b12_ds = resample_to_10m(b12_ds, target_shape)

            # Obtener datos como numpy arrays
            b02_data = datasets["B02"].values[0]  # Remover dimensión de banda
            b03_data = datasets["B03"].values[0]
            b04_data = datasets["B04"].values[0]
            b08_data = datasets["B08"].values[0]
            b11_data = b11_ds.values[0]
            b12_data = b12_ds.values[0]

            # Obtener transformación y CRS de la primera banda
            transform = datasets["B02"].rio.transform()
            crs = datasets["B02"].rio.crs

            # Cerrar datasets
            for ds in datasets.values():
                ds.close()

            # Convertir de valores digitales a reflectancia 0-1
            # Sentinel-2 L2a tiene escala de 0-10000 para reflectancia
            b02_data = b02_data.astype(np.float32) / 10000.0
            b03_data = b03_data.astype(np.float32) / 10000.0
            b04_data = b04_data.astype(np.float32) / 10000.0
            b08_data = b08_data.astype(np.float32) / 10000.0
            b11_data = b11_data.astype(np.float32) / 10000.0
            b12_data = b12_data.astype(np.float32) / 10000.0

            # Clip a valores válidos
            b02_data = np.clip(b02_data, 0, 1)
            b03_data = np.clip(b03_data, 0, 1)
            b04_data = np.clip(b04_data, 0, 1)
            b08_data = np.clip(b08_data, 0, 1)
            b11_data = np.clip(b11_data, 0, 1)
            b12_data = np.clip(b12_data, 0, 1)

            return BandData(
                b02=b02_data,
                b03=b03_data,
                b04=b04_data,
                b08=b08_data,
                b11=b11_data,
                b12=b12_data,
                transform=transform,
                crs=crs,
            )

        except Exception as e:
            raise StacError(f"Error descargando bandas: {e}")

    def create_parcel_mask(
        self,
        shape: tuple[int, int],
        geometry: dict | None,
        bbox: list[float] | None,
        image_crs: Any,
        transform: Any,
    ) -> np.ndarray:
        """
        Crea una máscara booleana donde True = píxel dentro de la parcela.

        Args:
            shape: (height, width) de las bandas
            geometry: GeoJSON geometría de la parcela (en WGS84)
            bbox: BBOX en WGS84 [min_lon, min_lat, max_lon, max_lat]
            image_crs: CRS de la imagen (UTM)
            transform: Transform affine del raster

        Returns:
            np.ndarray boolean con forma (height, width)
            True = píxel dentro de la parcela, False = fuera

        Nota:
            Si no hay geometría, retorna máscara completa (todos True).
            La verificación se hace en WGS84 para evitar problemas de conversión
            entre diferentes zonas UTM.
            Este método puede ser lento para imágenes grandes (~70k píxeles).
        """
        import logging
        logger = logging.getLogger(__name__)
        from shapely.geometry import Point, shape as shapely_shape

        # Si no hay geometría, retornar máscara completa (True)
        if geometry is None:
            logger.warning("🔶 create_parcel_mask: geometry is None, retornando máscara completa")
            return np.ones(shape, dtype=bool)

        try:
            height, width = shape
            rows, cols = np.indices((height, width))

            # LOG: Mostrar información de la imagen
            logger.info(f"📐 Image shape: {shape}, CRS: {image_crs}")
            logger.info(f"📐 Affine transform: {list(transform)[:6]}")
            logger.info(f"📐 BBOX recibido: {bbox}")

            # LOG: Mostrar bounds de la geometría
            geom_wgs84 = shapely_shape(geometry)
            geom_bounds = geom_wgs84.bounds
            logger.info(f"📐 Geometría bounds (WGS84): {geom_bounds}")

            # Paso 1: Convertir coordenadas de píxel a UTM (CRS de la imagen)
            x_coords_utm = transform[2] + cols * transform[0]
            y_coords_utm = transform[5] + rows * transform[4]

            # LOG: Mostrar esquinas de la imagen en UTM
            logger.info(f"📐 Esquinas UTM: TL=({x_coords_utm[0,0]:.2f}, {y_coords_utm[0,0]:.2f}) "
                       f"BR=({x_coords_utm[-1,-1]:.2f}, {y_coords_utm[-1,-1]:.2f})")

            # Paso 2: Convertir coordenadas UTM a WGS84
            image_crs_obj = CRS.from_user_input(image_crs)
            wgs84_crs = CRS.from_epsg(4326)

            transformer_to_wgs84 = Transformer.from_crs(image_crs_obj, wgs84_crs, always_xy=True)

            # Transformar todas las coordenadas (flatten para transformar)
            lons_flat, lats_flat = transformer_to_wgs84.transform(
                x_coords_utm.flatten(), y_coords_utm.flatten()
            )

            # LOG: Mostrar esquinas de la imagen en WGS84
            logger.info(f"📐 Esquinas WGS84: TL=({lons_flat[0]:.6f}, {lats_flat[0]:.6f}) "
                       f"BR=({lons_flat[-1]:.6f}, {lats_flat[-1]:.6f})")

            # Crear array booleano para la máscara
            mask_flat = np.zeros(len(lons_flat), dtype=bool)

            # Verificar contención punto por punto
            # Note: Esto es lento pero preciso. Para 68k píxeles toma ~2-3 segundos.
            for i in range(len(lons_flat)):
                point = Point(float(lons_flat[i]), float(lats_flat[i]))
                mask_flat[i] = geom_wgs84.contains(point)

            # LOG: Estadísticas de la máscara
            pixels_inside = np.sum(mask_flat)
            total_pixels = len(mask_flat)
            percentage = (pixels_inside / total_pixels) * 100
            logger.info(f"📊 Máscara: {pixels_inside}/{total_pixels} píxeles dentro ({percentage:.1f}%)")

            return mask_flat.reshape(shape).astype(bool)

        except Exception as e:
            logger.error(f"❌ Error en create_parcel_mask: {e}")
            # En caso de error, retornar máscara completa (no filtrar)
            # Esto permite que el análisis continúe aunque la máscara falle
            return np.ones(shape, dtype=bool)


def get_pixel_area_m2(transform: Any, crs: Any, lat: float = -35.0) -> float:
    """
    Calcula el área de un píxel en metros cuadrados.

    Usa el transform affine para obtener el tamaño exacto del píxel.

    Args:
        transform: Transformación affine del raster (rasterio)
        crs: Sistema de referencia de coordenadas
        lat: Latitud aproximada del área de estudio (para proyecciones lat/lon)

    Returns:
        Área del píxel en m²
    """
    if transform is not None:
        # El transform affine tiene formato (a, b, c, d, e, f)
        # donde a = pixel width, e = -pixel height (usualmente)
        pixel_width = abs(transform[0])
        pixel_height = abs(transform[4])
        return pixel_width * pixel_height
    else:
        # Fallback: Sentinel-2 L2A tiene 10m de resolución
        return 100.0
