"""
Cliente del servicio WFS de ARBA.

Permite obtener la geometría de una parcela catastral a partir
de su número de partida.
"""
from __future__ import annotations

import json
import requests
from typing import Any
from dataclasses import dataclass
from pathlib import Path
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


class PartidaParser:
    """
    Parser para partidas ARBA en múltiples formatos.

    Soporta los siguientes formatos:
    - 002004606 (9 dígitos: partido + partida)
    - 002-004606-0 (con guiones y verificador)
    - 0020046060 (10 dígitos: incluye verificador)
    - 002-004606 (sin verificador)
    - 00200460 (8 dígitos: partido + 5 dígitos, se completa a 6)
    - 4606 (solo partida, usa partido por defecto 002)
    """

    # Partido por defecto (Alberti)
    DEFAULT_PARTIDO = "002"

    def __init__(self, json_path: str | Path | None = None):
        """
        Inicializa el parser cargando los códigos de partidos.

        Args:
            json_path: Ruta al JSON de códigos de partidos.
                      Si es None, busca en sat-analysis/codigos_partidos_arba.json
        """
        self._partidos = self._load_partidos(json_path)

    def _load_partidos(self, json_path: str | Path | None) -> dict[str, str]:
        """Carga el diccionario de códigos de partidos desde JSON."""
        if json_path is None:
            # Buscar en sat-analysis/ (directorio padre del src/)
            try:
                # Primero intentar desde la ubicación del script
                script_dir = Path(__file__).parent.parent.parent.parent
                json_path = script_dir / "codigos_partidos_arba.json"
            except Exception:
                # Fallback a ruta relativa
                json_path = Path("codigos_partidos_arba.json")

        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("partidos", {})
        except FileNotFoundError:
            # Si no existe el JSON, retornar diccionario vacío
            # (fallback a comportamiento legacy)
            return {}
        except json.JSONDecodeError:
            return {}

    def parse(self, partida_input: str) -> "PartidaARBA":
        """
        Parsea una partida en cualquier formato aceptado.

        Args:
            partida_input: "002004606", "002-004606-0", "4606", etc.

        Returns:
            PartidaARBA con componentes parseados

        Raises:
            ValueError: Si el formato es inválido o el código de partido no existe
        """
        from ..models.schemas import PartidaARBA

        # Limpiar guiones y espacios
        limpia = partida_input.replace("-", "").strip().upper()

        # Validar que sean solo dígitos
        if not limpia.isdigit():
            raise ValueError(f"Partida inválida: {partida_input}. Debe contener solo dígitos.")

        # Caso 1: Solo partida individual (legacy, 1-6 dígitos)
        if len(limpia) <= 6:
            # Usar partido por defecto (002 Alberti)
            partida = limpia.zfill(6)
            codigo_partido = self.DEFAULT_PARTIDO
            verificador = None

        # Caso 2: 8 dígitos (partido + partida de 5 dígitos, completar a 6)
        elif len(limpia) == 8:
            codigo_partido = limpia[:3]
            partida = limpia[3:8].zfill(6)  # Completar a 6 dígitos
            verificador = None

        # Caso 3: 9 dígitos (partido + partida, sin verificador)
        elif len(limpia) == 9:
            codigo_partido = limpia[:3]
            partida = limpia[3:9]
            verificador = None

        # Caso 4: 10 dígitos (partido + partida + verificador)
        elif len(limpia) == 10:
            codigo_partido = limpia[:3]
            partida = limpia[3:9]
            verificador = limpia[9]

        else:
            raise ValueError(
                f"Longitud inválida: {len(limpia)}. "
                "Debe ser 1-6 (partida), 8 (partido+5dígitos), 9 (partido+partida), o 10 dígitos."
            )

        # Validar código de partido si tenemos el JSON cargado
        if self._partidos and codigo_partido not in self._partidos:
            partidos_validos = ", ".join(list(self._partidos.keys())[:5])
            raise ValueError(
                f"Código de partido inválido: {codigo_partido}. "
                f"Use un código válido (ej: {self.DEFAULT_PARTIDO} para Alberti). "
                f"Ejemplos: {partidos_validos}, ..."
            )

        nombre_partido = self._partidos.get(codigo_partido, f"Partido {codigo_partido}")

        # Formato completo para display
        verif_str = verificador if verificador else "?"
        formato_completo = f"{codigo_partido}-{partida}-{verif_str}"

        return PartidaARBA(
            codigo_partido=codigo_partido,
            nombre_partido=nombre_partido,
            partida_individual=partida,
            verificador=verificador,
            formato_completo=formato_completo,
        )

    def set_default_partido(self, codigo: str) -> None:
        """
        Establece partido por defecto para partidas sin código.

        Args:
            codigo: Código de partido de 3 dígitos

        Raises:
            ValueError: Si el código de partido no existe
        """
        if self._partidos and codigo not in self._partidos:
            raise ValueError(f"Código de partido inválido: {codigo}")
        self.DEFAULT_PARTIDO = codigo


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

    def get_parcel_geometry(self, partida: str | "PartidaARBA") -> ParcelData | None:
        """
        Obtiene la geometría de una parcela desde ARBA WFS.

        Args:
            partida: Número de partida catastral (ej: "4606", "002004606")
                     o PartidaARBA parseado con codigo_partido + partida_individual

        Returns:
            ParcelData con la geometría y bbox, o None si no se encuentra

        Raises:
            ArbaError: Si hay un error en la consulta

        Nota:
            El campo 'pda' en ARBA WFS almacena 9 dígitos: partido (3) + partida (6).
            El campo 'partido' NO existe como propiedad filtrable en el WFS.
            Ejemplo: pda='016001605' donde 016 es el partido y 001605 la partida.
        """
        from ..models.schemas import PartidaARBA

        # Si viene un string, intentar parsear para extraer componentes
        partida_9_digitos = None  # Formato: PPPSSSSSS (partido + partida)
        partida_str = partida

        if isinstance(partida, str):
            # Intentar parsear para validar formato
            parser = PartidaParser()
            try:
                partida_arba = parser.parse(partida)
                # ARBA espera pda con 9 dígitos: partido (3) + partida (6)
                partida_9_digitos = partida_arba.partida_completa
                partida_str = partida_arba.formato_completo
            except ValueError:
                # Si falla el parseo, usar directamente (legacy)
                # Asumir formato de 9 dígitos o completar con partido default
                limpia = partida.replace("-", "").strip()
                if len(limpia) == 9:
                    partida_9_digitos = limpia
                elif len(limpia) <= 6:
                    # Usar partido default (002 Alberti)
                    partida_9_digitos = f"002{limpia.zfill(6)}"
                else:
                    partida_9_digitos = limpia[:9]
                partida_str = partida_9_digitos
        elif isinstance(partida, PartidaARBA):
            partida_9_digitos = partida.partida_completa
            partida_str = partida.formato_completo

        # ARBA WFS espera el campo 'pda' con 9 dígitos (partido + partida)
        # El campo 'partido' no existe como propiedad filtrable
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": "idera:Parcela",
            "outputFormat": "application/json",
            "CQL_FILTER": f"pda='{partida_9_digitos}'",
        }

        try:
            response = requests.get(
                self.wfs_url, params=params, timeout=self.timeout
            )
            response.raise_for_status()
        except requests.Timeout:
            raise ArbaError(f"Timeout al consultar ARBA para partida {partida_str}")
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
            raise ArbaError(f"Feature sin geometría para partida {partida_str}")

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
            partida=partida_str,
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
        import logging
        logger = logging.getLogger(__name__)

        # Si no hay CRS especificado o no es EPSG:5347, retornar original
        if not crs or "5347" not in crs:
            logger.warning(f"🔶 CRS no es EPSG:5347: {crs}, retornando geometría original")
            return geometry

        geom_type = geometry.get("type")
        coordinates = geometry.get("coordinates", [])

        # LOG: Mostrar primeras coordenadas originales (UTM)
        if geom_type == "Polygon" and coordinates:
            first_ring = coordinates[0]
            if first_ring:
                orig_x, orig_y = first_ring[0][0], first_ring[0][1]
                logger.info(f"🔍 ARBA UTM orig: x={orig_x:.2f}, y={orig_y:.2f} (CRS: {crs})")

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

            # LOG: Mostrar primeras coordenadas transformadas (WGS84)
            if geom_type == "Polygon" and transformed_coords:
                first_ring = transformed_coords[0]
                if first_ring:
                    trans_lon, trans_lat = first_ring[0][0], first_ring[0][1]
                    logger.info(f"✅ ARBA WGS84 trans: lon={trans_lon:.6f}, lat={trans_lat:.6f}")

            return {
                "type": geom_type,
                "coordinates": transformed_coords
            }

        except Exception as e:
            logger.error(f"❌ Error transformando geometría: {e}")
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
