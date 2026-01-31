#!/usr/bin/env python3
"""
config - Configuración centralizada del proyecto

Este módulo define las rutas a los recursos del proyecto.
"""

from pathlib import Path

# Directorio base del proyecto
PROJECT_ROOT = Path(__file__).parent.parent

# Directorios de datos
DATA_DIR = PROJECT_ROOT / "data"
INDEXES_DIR = DATA_DIR / "indexes"
CACHE_DIR = DATA_DIR / "cache"
CONFIG_DIR = PROJECT_ROOT / "config"

# Asegurar que los directorios existen
DATA_DIR.mkdir(exist_ok=True)
INDEXES_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)

# Archivos de bases de datos
DEFAULT_DB_PATH = DATA_DIR / "normativas.db"

# Archivos de índices
BOLETINES_INDEX = INDEXES_DIR / "boletines_index.json"
NORMATIVAS_INDEX = INDEXES_DIR / "normativas_index.json"
MONTOS_INDEX = INDEXES_DIR / "montos_index.json"

# Archivos de configuración
SOURCES_FILE = CONFIG_DIR / "sources.yaml"
SOURCES_USER_FILE = CONFIG_DIR / "sources_user.yaml"
USER_SOURCES_FILE = SOURCES_USER_FILE  # Alias para compatibilidad con web_scraper

# Directorio de boletines
BOLETINES_DIR = PROJECT_ROOT / "boletines"


def get_db_path(db_name: str = "normativas.db") -> Path:
    """
    Retorna la ruta completa a una base de datos.

    Args:
        db_name: Nombre del archivo de base de datos

    Returns:
        Path completo al archivo en data/
    """
    return DATA_DIR / db_name


def get_index_path(index_name: str) -> Path:
    """
    Retorna la ruta completa a un archivo de índice.

    Args:
        index_name: Nombre del archivo de índice

    Returns:
        Path completo al archivo en data/indexes/
    """
    return INDEXES_DIR / index_name
