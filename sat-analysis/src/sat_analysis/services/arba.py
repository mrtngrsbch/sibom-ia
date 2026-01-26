"""
Cliente del servicio WFS de ARBA.

Permite obtener la geometría de una parcela catastral a partir
de su número de partida.
"""
import requests
from typing import Any
from dataclasses import dataclass
from pyproj import Transformer


@dataclass(frozen=True)
class ParcelData:
    """Datos de una parcela catastral."""

    partida: str
    geometry: dict  # GeoJSON Geometry
    bbox: list[float]  # [min_lon, min_lat, max_lon, max_lat]
    area_approx_hectares: float | None = None


class ArbaError(Exception):
    """Error al consultar el servicio WFS de ARBA."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class ArbaService:
    """Cliente del servicio WFS de ARBA."""

    def __init__(self, wfs_url: str = "https://geo.arba.gov.ar/geoserver/idera/wfs"):
        """
        Inicializa el cliente ARBA.

        Args:
            wfs_url: URL del servicio WFS de ARBA
        """
        self.wfs_url = wfs_url
        self.timeout = 15

    def get_parcel_geometry(self, partida: str) -> ParcelData | None:
        """
        Obtiene la geometría de una parcela desde ARBA WFS.

        Args:
            partida: Número de partida catastral (ej: "4606")

        Returns:
            ParcelData con la geometría y bbox, o None si no se encuentra

        Raises:
            ArbaError: Si hay un error en la consulta
        """
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": "idera:Parcela",
            "outputFormat": "application/json",
            "CQL_FILTER": f"pda='{partida}'",
        }

        try:
            response = requests.get(
                self.wfs_url, params=params, timeout=self.timeout
            )
            response.raise_for_status()
        except requests.Timeout:
            raise ArbaError(f"Timeout al consultar ARBA para partida {partida}")
        except requests.HTTPError as e:
            raise ArbaError(
                f"Error HTTP al consultar ARBA: {e.response.status_code}",
                status_code=e.response.status_code,
            )
        except requests.RequestException as e:
            raise ArbaError(f"Error de red al consultar ARBA: {e}")

        # Parsear respuesta JSON
        try:
            data = response.json()
        except ValueError as e:
            raise ArbaError(f"Respuesta inválida de ARBA (no es JSON): {e}")

        # Verificar que haya features
        features = data.get("features", [])
        if not features:
            return None

        # Obtener el primer feature (debería haber solo uno)
        feature = features[0]
        geometry = feature.get("geometry")
        properties = feature.get("properties", {})

        if not geometry:
            raise ArbaError(f"Feature sin geometría para partida {partida}")

        # Extraer CRS de la respuesta
        crs = data.get("crs")
        crs_name = None
        if isinstance(crs, dict):
            props = crs.get("properties", {})
            crs_name = props.get("name", "")

        # Extraer bbox del polígono (convertir de UTM a lat/long)
        bbox = self._extract_bbox(geometry, crs=crs_name)

        # Convertir geometría a WGS84 para usarla en la máscara
        geometry_wgs84 = self._convert_geometry_to_wgs84(geometry, crs=crs_name)

        # Obtener superficie desde ARA1 (en m²) si está disponible
        # ARA1 viene como float en JSON (ej: 3336499.29 = 333.65 ha)
        area_m2 = None
        ara1_value = properties.get("ara1")
        if ara1_value is not None:
            try:
                # ARA1 viene como float desde el JSON de ARBA
                # Direct conversión a float
                area_m2 = float(ara1_value)
            except (ValueError, TypeError):
                pass

        # Calcular área aproximada solo si no tenemos ARA1
        area_hectares = None
        if area_m2 is not None:
            area_hectares = area_m2 / 10000  # m² a hectáreas
        else:
            # Fallback a cálculo aproximado por bbox
            area_hectares = self._calculate_approx_area(geometry)

        return ParcelData(
            partida=partida,
            geometry=geometry_wgs84,
            bbox=bbox,
            area_approx_hectares=area_hectares,
        )

    def _convert_geometry_to_wgs84(self, geometry: dict, crs: str | None = None) -> dict:
        """
        Convierte una geometría GeoJSON de UTM a WGS84.

        Args:
            geometry: Objeto geometría GeoJSON (en UTM)
            crs: Sistema de referencia de coordenadas original (ej: "EPSG:5347")

        Returns:
            Nueva geometría GeoJSON con coordenadas en WGS84
        """
        # Si no hay CRS especificado o no es EPSG:5347, retornar original
        if not crs or "5347" not in crs:
            return geometry

        geom_type = geometry.get("type")
        coordinates = geometry.get("coordinates", [])

        try:
            # Crear transformador de UTM zona 20S a WGS84
            transformer = Transformer.from_crs("EPSG:5347", "EPSG:4326", always_xy=True)

            def transform_coord(coord):
                """Transforma una coordenada (x, y) o (x, y, z)."""
                x, y = coord[0], coord[1]
                lon, lat = transformer.transform(x, y)
                return [lon, lat] + list(coord[2:]) if len(coord) > 2 else [lon, lat]

            def transform_coords_recursive(coords, geom_type):
                """Transforma coordenadas recursivamente según el tipo de geometría."""
                if geom_type == "Point":
                    return transform_coord(coords)
                elif geom_type == "MultiPoint":
                    return [transform_coord(c) for c in coords]
                elif geom_type == "LineString":
                    return [transform_coord(c) for c in coords]
                elif geom_type == "MultiLineString":
                    return [[transform_coord(c) for c in line] for line in coords]
                elif geom_type == "Polygon":
                    # Polygon: [[[x1, y1], [x2, y2], ...]]
                    return [[transform_coord(c) for c in ring] for ring in coords]
                elif geom_type == "MultiPolygon":
                    # MultiPolygon: [[[[x1, y1], ...]], ...]
                    return [[[transform_coord(c) for c in ring] for ring in poly] for poly in coords]
                else:
                    return coords

            transformed_coords = transform_coords_recursive(coordinates, geom_type)

            return {
                "type": geom_type,
                "coordinates": transformed_coords
            }

        except Exception:
            # Si falla la conversión, retornar geometría original
            return geometry

    def _extract_bbox(self, geometry: dict, crs: str | None = None) -> list[float]:
        """
        Extrae el bounding box de una geometría GeoJSON y lo convierte a lat/long.

        Args:
            geometry: Objeto geometría GeoJSON
            crs: Sistema de referencia de coordenadas (ej: "EPSG:5347")

        Returns:
            [min_lon, min_lat, max_lon, max_lat] en WGS84 (lat/long)
        """
        geom_type = geometry.get("type")
        coordinates = geometry.get("coordinates", [])

        all_coords = []

        if geom_type == "Polygon":
            all_coords = coordinates[0]  # Anillo exterior
        elif geom_type == "MultiPolygon":
            # Tomar el primer polígono
            all_coords = coordinates[0][0] if coordinates else []
        else:
            # Punto, LineString, etc.
            all_coords = coordinates if isinstance(coordinates[0], list) else [coordinates]

        if not all_coords:
            return [0, 0, 0, 0]

        # Las coordenadas de ARBA vienen en UTM (EPSG:5347 para Buenos Aires)
        # Necesitamos convertirlas a WGS84 (lat/long)
        if crs and "5347" in crs:
            try:
                # Crear transformador de UTM zona 20S a WGS84
                transformer = Transformer.from_crs("EPSG:5347", "EPSG:4326", always_xy=True)

                # Transformar todas las coordenadas
                transformed_coords = []
                for x, y in all_coords:
                    lon, lat = transformer.transform(x, y)
                    transformed_coords.append((lon, lat))

                all_coords = transformed_coords
            except Exception:
                pass  # Usar coordenadas originales si falla la conversión

        lons = [c[0] for c in all_coords]
        lats = [c[1] for c in all_coords]

        return [min(lons), min(lats), max(lons), max(lats)]

    def _calculate_approx_area(self, geometry: dict) -> float | None:
        """
        Calcula el área aproximada de la parcela en hectáreas.

        Usando una aproximación basada en el bbox.
        1 grado ≈ 111 km a latitud media de Buenos Aires (-35°)

        Args:
            geometry: Objeto geometría GeoJSON

        Returns:
            Área aproximada en hectáreas, o None si no se puede calcular
        """
        bbox = self._extract_bbox(geometry)
        lon_diff = bbox[2] - bbox[0]
        lat_diff = bbox[3] - bbox[1]

        # A latitud -35°, 1 grado de latitud ≈ 111 km
        # 1 grado de longitud ≈ 111 km * cos(35°) ≈ 91 km
        lat_km = lat_diff * 111
        lon_km = lon_diff * 91

        area_km2 = lat_km * lon_km
        return area_km2 * 100  # km² a hectáreas
