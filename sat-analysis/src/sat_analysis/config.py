"""
Configuración del sistema sat-analysis.

Usa pydantic-settings para cargar configuración desde:
1. Archivo thresholds.yaml (umbrales de clasificación)
2. Variables de entorno (prefijo SAT_ANALYSIS_)
3. Valores por defecto (hardcoded)
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Any
import yaml


class Settings(BaseSettings):
    """Configuración de la aplicación."""

    # URLs de servicios externos
    arba_wfs_url: str = "https://geo.arba.gov.ar/geoserver/idera/wfs"
    stac_url: str = "https://planetarycomputer.microsoft.com/api/stac/v1"

    # Colección STAC para Sentinel-2
    sentinel_collection: str = "sentinel-2-l2a"

    # Configuración de búsqueda de imágenes
    max_cloud_cover: int = 20  # Porcentaje máximo de nubes
    max_images: int = 10  # Máximo de imágenes a procesar por análisis

    # Configuración de clasificación (umbrales ajustados para humedales de Argentina)
    water_ndwi_threshold: float = 0.15      # NDWI > agua
    water_mndwi_threshold: float = 0.25     # MNDWI > agua turbia
    wetland_ndvi_threshold: float = 0.35    # NDVI > vegetación húmeda
    wetland_ndmi_threshold: float = 0.10    # NDMI > humedad
    wetland_ndwi_threshold: float = -0.6    # NDWI > (permite vegetación húmeda)
    vegetation_ndvi_threshold: float = 0.5  # NDVI > vegetación seca
    vegetation_ndmi_threshold: float = 0.2  # NDMI < límite superior

    # Configuración de logging
    log_level: str = "INFO"

    # Directorio de salida
    output_dir: str = "./results"

    model_config = SettingsConfigDict(
        env_prefix="SAT_ANALYSIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def _load_thresholds_from_yaml() -> dict[str, Any] | None:
    """
    Carga umbrales desde archivo thresholds.yaml.

    Returns:
        Dict con umbrales o None si el archivo no existe.
    """
    # Buscar thresholds.yaml en el directorio del paquete
    script_dir = Path(__file__).parent.parent.parent
    yaml_path = script_dir / "thresholds.yaml"

    if not yaml_path.exists():
        return None

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Mapear estructura YAML a nombres de variables
        thresholds = {}

        if "water" in data:
            thresholds["water_ndwi_threshold"] = data["water"].get("ndwi_threshold", 0.15)
            thresholds["water_mndwi_threshold"] = data["water"].get("mndwi_threshold", 0.25)

        if "wetland" in data:
            thresholds["wetland_ndvi_threshold"] = data["wetland"].get("ndvi_threshold", 0.35)
            thresholds["wetland_ndmi_threshold"] = data["wetland"].get("ndmi_threshold", 0.10)
            thresholds["wetland_ndwi_threshold"] = data["wetland"].get("ndwi_threshold", -0.6)

        if "vegetation" in data:
            thresholds["vegetation_ndvi_threshold"] = data["vegetation"].get("ndvi_threshold", 0.5)
            thresholds["vegetation_ndmi_threshold"] = data["vegetation"].get("ndmi_threshold", 0.2)

        return thresholds

    except Exception:
        # Si hay error leyendo YAML, usar valores por defecto
        return None


# Instancia global de configuración
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    Retorna la instancia de configuración (singleton).

    Prioridad de carga:
    1. thresholds.yaml (umbrales de clasificación)
    2. Variables de entorno (SAT_ANALYSIS_*)
    3. Valores por defecto
    """
    global _settings
    if _settings is None:
        # Primero cargar umbrales desde YAML si existe
        yaml_thresholds = _load_thresholds_from_yaml()

        if yaml_thresholds:
            # Crear Settings con valores de YAML
            _settings = Settings(**yaml_thresholds)
        else:
            # Usar valores por defecto (o variables de entorno)
            _settings = Settings()

    return _settings
