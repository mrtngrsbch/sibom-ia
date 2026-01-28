"""Fixtures compartidas para tests de sat-analysis."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from rasterio.transform import from_bounds
from shapely.geometry import Polygon, shape as shapely_shape

# Directorio de fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_polygon_wgs84() -> dict[str, Any]:
    """Geometría simple en WGS84 para testing.

    Corresponde a un área aproximada de 2km × 2km en la provincia de
    Buenos Aires, Argentina (zona de humedales).
    """
    return {
        "type": "Polygon",
        "coordinates": [[
            [-62.5, -35.33],
            [-62.5, -35.31],
            [-62.48, -35.31],
            [-62.48, -35.33],
            [-62.5, -35.33]
        ]]
    }


@pytest.fixture
def sample_multipolygon_wgs84() -> dict[str, Any]:
    """Geometría MultiPolygon en WGS84 para testing.

    Simula una parcela fragmentada en dos polígonos separados.
    """
    return {
        "type": "MultiPolygon",
        "coordinates": [
            [[  # Polígono 1
                [-62.5, -35.33],
                [-62.5, -35.32],
                [-62.49, -35.32],
                [-62.49, -35.33],
                [-62.5, -35.33]
            ]],
            [[  # Polígono 2
                [-62.49, -35.315],
                [-62.49, -35.31],
                [-62.48, -35.31],
                [-62.48, -35.315],
                [-62.49, -35.315]
            ]]
        ]
    }


@pytest.fixture
def sample_bbox() -> list[float]:
    """BBOX simple que contiene la geometría de prueba.

    Formato: [min_lon, min_lat, max_lon, max_lat]
    """
    return [-62.51, -35.34, -62.47, -35.30]


@pytest.fixture
def sample_affine_transform() -> tuple:
    """Transform affine típico de Sentinel-2.

    Corresponde a una imagen de 100×100 píxeles con resolución 10m
    en UTM Zone 20S (EPSG:32720).
    """
    # from_bounds(west, south, east, north, width, height)
    # 100 píxeles × 10m = 1000m de ancho/alto
    return from_bounds(500000, 6000000, 501000, 6001000, 100, 100)


@pytest.fixture
def sample_shape() -> tuple[int, int]:
    """Shape típico de imagen recortada.

    Valores basados en logs reales: 258×332 píxeles.
    """
    return (258, 332)


@pytest.fixture
def sample_small_shape() -> tuple[int, int]:
    """Shape pequeño para tests rápidos."""
    return (50, 50)


@pytest.fixture
def arba_polygon_017() -> dict[str, Any]:
    """Geometría real de la partida 0170012200 (Carlos Tejedor).

    Extraída de ARBA para testing con datos reales.
    """
    return {
        "type": "Polygon",
        "coordinates": [[
            [-62.516951550665944, -35.33736201380778],
            [-62.516951550665944, -35.30950381584809],
            [-62.48119013708994, -35.30950381584809],
            [-62.48119013708994, -35.33736201380778],
            [-62.516951550665944, -35.33736201380778]
        ]]
    }


@pytest.fixture
def arba_bbox_017() -> list[float]:
    """BBOX real de la partida 0170012200."""
    return [-62.516951550665944, -35.33736201380778, -62.48119013708994, -35.30950381584809]


@pytest.fixture
def sample_expected_mask_path() -> Path:
    """Ruta al archivo de máscara esperada para tests de regresión."""
    return FIXTURES_DIR / "expected_masks" / "sample_mask.npz"


@pytest.fixture
def stac_service():
    """Instancia de StacService para testing."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

    from sat_analysis.services import StacService
    return StacService()


@pytest.fixture
def mock_sentinel_item():
    """Item STAC mock de Sentinel-2 para testing."""
    from datetime import datetime
    from pystac import Item, Asset

    item = Item(
        id="S2A_20HNG_20250101",
        geometry={
            "type": "Polygon",
            "coordinates": [[
                [-63.0, -36.0],
                [-63.0, -35.0],
                [-62.0, -35.0],
                [-62.0, -36.0],
                [-63.0, -36.0]
            ]]
        },
        bbox=[-63.0, -36.0, -62.0, -35.0],
        datetime=datetime.now(),
        properties={
            "eo:cloud_cover": 5.0,
            "platform": "sentinel-2a",
        },
        assets={}
    )
    return item


@pytest.fixture
def sample_sentinel_bands():
    """Bandas Sentinel-2 mock para testing.

    Crea arrays numpy simulando las bandas B02, B03, B04, B08, B11, B12.
    """
    shape = (50, 50)  # height, width

    # Valores típicos de reflectancia Sentinel-2 (0-1 escalado a 0-10000)
    np.random.seed(42)
    return type("Bands", (), {
        "b02": np.random.randint(0, 5000, shape, dtype=np.uint16),  # Blue
        "b03": np.random.randint(0, 6000, shape, dtype=np.uint16),  # Green
        "b04": np.random.randint(0, 7000, shape, dtype=np.uint16),  # Red
        "b08": np.random.randint(0, 8000, shape, dtype=np.uint16),  # NIR
        "b11": np.random.randint(0, 5000, shape, dtype=np.uint16),  # SWIR1
        "b12": np.random.randint(0, 4000, shape, dtype=np.uint16),  # SWIR2
    })()


@pytest.fixture
def sample_pixel_area() -> float:
    """Área de píxel en m² para Sentinel-2 (10m × 10m)."""
    return 100.0


@pytest.fixture
def image_crs_utm_20s() -> str:
    """CRS UTM Zone 20S (usado en Argentina)."""
    return "EPSG:32720"


@pytest.fixture
def wgs84_crs() -> str:
    """CRS WGS84."""
    return "EPSG:4326"


@pytest.fixture
def sample_class_thresholds():
    """Umbrales de clasificación para testing."""
    return {
        "water_ndwi_threshold": 0.15,
        "water_mndwi_threshold": 0.25,
        "wetland_ndvi_threshold": 0.35,
        "wetland_ndmi_threshold": 0.10,
        "wetland_ndwi_threshold": -0.6,
        "vegetation_ndvi_threshold": 0.5,
        "vegetation_ndmi_threshold": 0.2,
    }
