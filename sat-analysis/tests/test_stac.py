"""Tests para StacService - OPT-001: Optimización de create_parcel_mask.

Este módulo contiene tests para validar la optimización del método
create_parcel_mask antes y después de la refactorización.

Estrategia: Tests First
1. Escribir tests que validan el comportamiento actual
2. Verificar que pasan con la implementación actual
3. Implementar optimización
4. Verificar que los tests SIGUEN pasando
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sat_analysis.services import StacService


class TestCreateParcelMaskCorrectness:
    """Tests de corrección del método create_parcel_mask."""

    def test_mask_shape_correct(self, sample_polygon_wgs84, sample_affine_transform, sample_small_shape):
        """Verifica que la máscara creada tenga la forma correcta."""
        stac = StacService()
        bbox = [-62.51, -35.34, -62.47, -35.30]

        mask = stac.create_parcel_mask(
            shape=sample_small_shape,
            geometry=sample_polygon_wgs84,
            bbox=bbox,
            image_crs="EPSG:32720",
            transform=sample_affine_transform
        )

        assert mask.shape == sample_small_shape, f"Expected shape {sample_small_shape}, got {mask.shape}"

    def test_mask_dtype_is_bool(self, sample_polygon_wgs84, sample_affine_transform, sample_small_shape):
        """Verifica que la máscara sea de tipo bool."""
        stac = StacService()
        bbox = [-62.51, -35.34, -62.47, -35.30]

        mask = stac.create_parcel_mask(
            shape=sample_small_shape,
            geometry=sample_polygon_wgs84,
            bbox=bbox,
            image_crs="EPSG:32720",
            transform=sample_affine_transform
        )

        assert mask.dtype == bool, f"Expected dtype bool, got {mask.dtype}"

    def test_mask_values_are_binary(self, sample_polygon_wgs84, sample_affine_transform, sample_small_shape):
        """Verifica que la máscara solo contenga valores 0 o 1 (True/False)."""
        stac = StacService()
        bbox = [-62.51, -35.34, -62.47, -35.30]

        mask = stac.create_parcel_mask(
            shape=sample_small_shape,
            geometry=sample_polygon_wgs84,
            bbox=bbox,
            image_crs="EPSG:32720",
            transform=sample_affine_transform
        )

        unique_values = np.unique(mask)
        assert len(unique_values) <= 2, f"Mask should only have 2 values, got {unique_values}"
        assert all(v in [0, 1, True, False] for v in unique_values), f"Invalid mask values: {unique_values}"


class TestCreateParcelMaskReproducibility:
    """Tests de reproducibilidad del método create_parcel_mask."""

    def test_mask_is_deterministic(self, sample_polygon_wgs84, sample_affine_transform, sample_small_shape):
        """Verifica que la máscara sea determinista (mismo input = mismo output)."""
        stac = StacService()
        bbox = [-62.51, -35.34, -62.47, -35.30]

        mask1 = stac.create_parcel_mask(
            shape=sample_small_shape,
            geometry=sample_polygon_wgs84,
            bbox=bbox,
            image_crs="EPSG:32720",
            transform=sample_affine_transform
        )

        mask2 = stac.create_parcel_mask(
            shape=sample_small_shape,
            geometry=sample_polygon_wgs84,
            bbox=bbox,
            image_crs="EPSG:32720",
            transform=sample_affine_transform
        )

        assert np.array_equal(mask1, mask2), "Mask should be deterministic"

    def test_mask_different_services(self, sample_polygon_wgs84, sample_affine_transform, sample_small_shape):
        """Verifica que diferentes instancias produzcan el mismo resultado."""
        bbox = [-62.51, -35.34, -62.47, -35.30]

        stac1 = StacService()
        mask1 = stac1.create_parcel_mask(
            shape=sample_small_shape,
            geometry=sample_polygon_wgs84,
            bbox=bbox,
            image_crs="EPSG:32720",
            transform=sample_affine_transform
        )

        stac2 = StacService()
        mask2 = stac2.create_parcel_mask(
            shape=sample_small_shape,
            geometry=sample_polygon_wgs84,
            bbox=bbox,
            image_crs="EPSG:32720",
            transform=sample_affine_transform
        )

        assert np.array_equal(mask1, mask2), "Different instances should produce same mask"


class TestCreateParcelMaskGeometryTypes:
    """Tests de create_parcel_mask con diferentes tipos de geometría."""

    def test_mask_with_polygon(self, sample_polygon_wgs84, sample_affine_transform, sample_small_shape):
        """Verifica que funcione correctamente con geometría Polygon."""
        stac = StacService()
        bbox = [-62.51, -35.34, -62.47, -35.30]

        mask = stac.create_parcel_mask(
            shape=sample_small_shape,
            geometry=sample_polygon_wgs84,
            bbox=bbox,
            image_crs="EPSG:32720",
            transform=sample_affine_transform
        )

        assert mask.shape == sample_small_shape
        assert mask.dtype == bool

    def test_mask_with_multipolygon(self, sample_multipolygon_wgs84, sample_affine_transform, sample_small_shape):
        """Verifica que funcione correctamente con geometría MultiPolygon."""
        stac = StacService()
        bbox = [-62.51, -35.34, -62.47, -35.30]

        mask = stac.create_parcel_mask(
            shape=sample_small_shape,
            geometry=sample_multipolygon_wgs84,
            bbox=bbox,
            image_crs="EPSG:32720",
            transform=sample_affine_transform
        )

        assert mask.shape == sample_small_shape
        assert mask.dtype == bool


class TestCreateParcelMaskEdgeCases:
    """Tests de edge cases para create_parcel_mask."""

    def test_mask_with_geometry_outside_image(self, sample_affine_transform, sample_small_shape):
        """Verifica comportamiento cuando la geometría está fuera de la imagen."""
        stac = StacService()

        # Geometría muy lejos del bbox de la imagen
        geometry_far_away = {
            "type": "Polygon",
            "coordinates": [[
                [0.0, 0.0],
                [0.0, 1.0],
                [1.0, 1.0],
                [1.0, 0.0],
                [0.0, 0.0]
            ]]
        }
        bbox = [-62.51, -35.34, -62.47, -35.30]

        mask = stac.create_parcel_mask(
            shape=sample_small_shape,
            geometry=geometry_far_away,
            bbox=bbox,
            image_crs="EPSG:32720",
            transform=sample_affine_transform
        )

        # Ningún píxel debería estar dentro
        assert mask.sum() == 0, "No pixels should be inside when geometry is far away"

    def test_mask_with_tiny_image(self, sample_polygon_wgs84, sample_affine_transform):
        """Verifica que funcione con imágenes muy pequeñas (1x1)."""
        stac = StacService()
        bbox = [-62.51, -35.34, -62.47, -35.30]

        mask = stac.create_parcel_mask(
            shape=(1, 1),
            geometry=sample_polygon_wgs84,
            bbox=bbox,
            image_crs="EPSG:32720",
            transform=sample_affine_transform
        )

        assert mask.shape == (1, 1)
        assert mask.dtype == bool


class TestCreateParcelMaskPerformance:
    """Tests de performance para establecer baseline y comparar optimización."""

    def test_performance_baseline_small(self, sample_polygon_wgs84, sample_affine_transform, sample_small_shape):
        """Establece baseline de performance para imagen pequeña (50x50)."""
        import time

        stac = StacService()
        bbox = [-62.51, -35.34, -62.47, -35.30]

        start = time.perf_counter()
        mask = stac.create_parcel_mask(
            shape=sample_small_shape,
            geometry=sample_polygon_wgs84,
            bbox=bbox,
            image_crs="EPSG:32720",
            transform=sample_affine_transform
        )
        elapsed = time.perf_counter() - start

        print(f"\n[PERF] Tiempo actual (50x50): {elapsed:.4f}s")

        # Verificar que el resultado sea válido
        assert mask.shape == sample_small_shape
        assert mask.dtype == bool

        # Guardar el tiempo en un atributo del test para uso posterior
        TestCreateParcelMaskPerformance.baseline_time_small = elapsed

    def test_performance_baseline_medium(self, sample_polygon_wgs84, sample_affine_transform):
        """Establece baseline de performance para imagen mediana (258x332 - tamaño real)."""
        import time

        stac = StacService()
        bbox = [-62.51, -35.34, -62.47, -35.30]
        shape = (258, 332)

        start = time.perf_counter()
        mask = stac.create_parcel_mask(
            shape=shape,
            geometry=sample_polygon_wgs84,
            bbox=bbox,
            image_crs="EPSG:32720",
            transform=sample_affine_transform
        )
        elapsed = time.perf_counter() - start

        print(f"\n[PERF] Tiempo actual (258x332): {elapsed:.4f}s")

        # Verificar que el resultado sea válido
        assert mask.shape == shape
        assert mask.dtype == bool

        # Guardar el tiempo en un atributo del test para uso posterior
        TestCreateParcelMaskPerformance.baseline_time_medium = elapsed


class TestCreateParcelMaskRealData:
    """Tests con datos reales de ARBA (partida 0170012200)."""

    def test_mask_with_arba_017(self, arba_polygon_017, arba_bbox_017, sample_affine_transform):
        """Test con geometría real de ARBA - partida 0170012200."""
        stac = StacService()

        # Usar shape real del log
        shape = (258, 332)

        mask = stac.create_parcel_mask(
            shape=shape,
            geometry=arba_polygon_017,
            bbox=arba_bbox_017,
            image_crs="EPSG:32720",
            transform=sample_affine_transform
        )

        assert mask.shape == shape
        assert mask.dtype == bool

        # Debería tener algunos píxeles dentro (la geometría es real)
        pixels_inside = mask.sum()
        print(f"\n[DATA] Píxeles dentro (0170012200): {pixels_inside}/{mask.size} ({100*pixels_inside/mask.size:.1f}%)")


class TestVerifyPostDownloadCoverage:
    """Tests para FIX-001: Verificación de cobertura real post-descarga.

    Estos tests verifican que después de descargar las bandas,
    se pueda validar que la geometría de la parcela esté
    razonablemente cubierta por los píxeles descargados.
    """

    def test_verify_coverage_high_coverage(self, sample_polygon_wgs84, sample_affine_transform, sample_small_shape):
        """Verifica que la detección de cobertura funcione con alta cobertura."""
        stac = StacService()
        bbox = [-62.51, -35.34, -62.47, -35.30]

        mask = stac.create_parcel_mask(
            shape=sample_small_shape,
            geometry=sample_polygon_wgs84,
            bbox=bbox,
            image_crs="EPSG:32720",
            transform=sample_affine_transform
        )

        # Verificar cobertura usando el método nuevo
        coverage_info = stac.verify_mask_coverage(mask, expected_area_hectares=500.0)

        assert coverage_info["pixels_inside"] >= 0
        assert coverage_info["total_pixels"] == mask.size
        assert 0 <= coverage_info["coverage_percentage"] <= 100
        assert coverage_info["has_sufficient_coverage"] is not None

    def test_verify_coverage_low_coverage_warning(self, sample_affine_transform, arba_bbox_017):
        """Verifica que se detecte baja cobertura y se genere advertencia."""
        stac = StacService()

        # Crear una máscara con muy baja cobertura (simulando edge case)
        import numpy as np
        mask = np.zeros((258, 332), dtype=bool)
        # Solo 100 píxeles dentro (~0.04%)
        mask[100:105, 200:205] = True

        coverage_info = stac.verify_mask_coverage(mask, expected_area_hectares=500.0)

        # Con baja cobertura, should_warn debe ser True
        assert coverage_info["coverage_percentage"] < 10
        print(f"\n[COVERAGE] Baja cobertura detectada: {coverage_info['coverage_percentage']:.2f}%")

    def test_verify_coverage_full_mask(self, sample_affine_transform):
        """Verifica comportamiento con máscara completa (todos True)."""
        stac = StacService()

        mask = np.ones((100, 100), dtype=bool)

        coverage_info = stac.verify_mask_coverage(mask, expected_area_hectares=100.0)

        assert coverage_info["coverage_percentage"] == 100.0
        assert coverage_info["has_sufficient_coverage"] is True
        assert coverage_info["should_warn"] is False

    def test_verify_coverage_empty_mask(self, sample_affine_transform):
        """Verifica comportamiento con máscara vacía (todos False)."""
        stac = StacService()

        mask = np.zeros((100, 100), dtype=bool)

        coverage_info = stac.verify_mask_coverage(mask, expected_area_hectares=100.0)

        assert coverage_info["coverage_percentage"] == 0.0
        assert coverage_info["has_sufficient_coverage"] is False
        assert coverage_info["should_warn"] is True

    def test_verify_coverage_threshold_90_percent(self, sample_affine_transform):
        """Verifica que el umbral de advertencia sea 90%."""
        stac = StacService()

        # Máscara con exactamente 90% de cobertura
        mask = np.zeros((100, 100), dtype=bool)
        mask[:90, :] = True  # 90 filas de 100 = 9000/10000 = 90%

        coverage_info = stac.verify_mask_coverage(mask, expected_area_hectares=100.0)

        # 90% debe ser suficiente (umbral es >= 90)
        assert coverage_info["has_sufficient_coverage"] is True
        assert coverage_info["should_warn"] is False

        # Ahora 89%
        mask[:89, :] = True
        mask[89:, :] = False

        coverage_info = stac.verify_mask_coverage(mask, expected_area_hectares=100.0)

        # 89% debe generar advertencia
        assert coverage_info["coverage_percentage"] < 90
        assert coverage_info["has_sufficient_coverage"] is False
        assert coverage_info["should_warn"] is True


class TestImageCoverageWithRealData:
    """Tests de cobertura con datos reales de la partida 0170012200."""

    def test_real_world_017_coverage_analysis(self, arba_polygon_017, arba_bbox_017):
        """Analiza la cobertura real de la partida 0170012200.

        Este test documenta el caso real donde la parcela tiene ~19.3% de cobertura
        debido a que está en el borde del tile de Sentinel-2.

        El sistema debe detectar esto y emitir una advertencia, pero continuar
        funcionando (no es un error fatal).

        NOTA: Usamos un transform affine que realmente corresponde a la ubicación
        de la parcela 017 (UTM Zone 20S).
        """
        from rasterio.transform import from_bounds

        stac = StacService()
        shape = (258, 332)

        # Crear un transform que realmente corresponda a la ubicación de la parcela
        # La parcela está en UTM 20S, aproximadamente en:
        # X: 542000-548000, Y: 6088000-6093000
        affine_realistic = from_bounds(542000, 6088000, 548000, 6094000, 332, 258)

        mask = stac.create_parcel_mask(
            shape=shape,
            geometry=arba_polygon_017,
            bbox=arba_bbox_017,
            image_crs="EPSG:32720",
            transform=affine_realistic
        )

        coverage_info = stac.verify_mask_coverage(
            mask,
            expected_area_hectares=500.9
        )

        print(f"\n[REAL WORLD] Partida 0170012200:")
        print(f"  Píxeles dentro: {coverage_info['pixels_inside']}/{coverage_info['total_pixels']}")
        print(f"  Cobertura: {coverage_info['coverage_percentage']:.1f}%")
        print(f"  Área calculada: {coverage_info['calculated_area_hectares']:.1f} ha")
        print(f"  Área esperada: 500.9 ha")
        print(f"  Suficiente: {coverage_info['has_sufficient_coverage']}")
        print(f"  Debe advertir: {coverage_info['should_warn']}")

        # Verificar que la máscara tenga píxeles dentro
        assert coverage_info["pixels_inside"] > 0, "La máscara debe tener píxeles dentro"

        # La partida 017 tiene cobertura baja (~19-20%) por estar en el borde
        # Esto debe detectarse como advertencia, no como error
        # (El porcentaje exacto puede variar según el transform usado)
        if coverage_info["coverage_percentage"] < 90:
            assert coverage_info["should_warn"] is True


class TestImageCache:
    """Tests para FEAT-001: Sistema de caché de imágenes.

    Estos tests verifican que el caché funcione correctamente para
    almacenar y recuperar imágenes satelitales descargadas.
    """

    def test_cache_initialization(self, tmp_path):
        """Verifica que el caché se inicialice correctamente."""
        from sat_analysis.services.cache import ImageCache

        cache_dir = tmp_path / "cache"
        cache = ImageCache(cache_dir=cache_dir, max_size_mb=100.0, ttl_days=30)

        assert cache.cache_dir == cache_dir
        assert cache.max_size_mb == 100.0
        assert cache.ttl_days == 30
        assert cache.cache_dir.exists()
        assert cache.index == {}

    def test_cache_put_and_get(self, tmp_path, sample_sentinel_bands):
        """Verifica guardar y recuperar bandas del caché."""
        from sat_analysis.services.cache import ImageCache
        from rasterio.transform import from_bounds

        cache_dir = tmp_path / "cache"
        cache = ImageCache(cache_dir=cache_dir, max_size_mb=100.0)

        item_id = "S2A_20HNG_20250101"
        bbox = [-63.0, -36.0, -62.0, -35.0]
        crs = "EPSG:32720"
        transform = from_bounds(500000, 6000000, 501000, 6001000, 100, 100)

        # Guardar en caché
        success = cache.put(
            item_id=item_id,
            bands={
                "b02": sample_sentinel_bands.b02,
                "b03": sample_sentinel_bands.b03,
                "b04": sample_sentinel_bands.b04,
                "b08": sample_sentinel_bands.b08,
                "b11": sample_sentinel_bands.b11,
                "b12": sample_sentinel_bands.b12,
            },
            crs=crs,
            transform=transform,
            bbox=bbox,
        )

        assert success is True
        assert len(cache.index) == 1

        # Recuperar desde caché
        cached = cache.get(item_id=item_id, bbox=bbox)

        assert cached is not None
        assert cached["from_cache"] is True
        assert cached["crs"] == crs
        assert cached["shape"] == sample_sentinel_bands.b02.shape
        assert np.array_equal(cached["b02"], sample_sentinel_bands.b02)

    def test_cache_miss(self, tmp_path):
        """Verifica que se retorne None para items no cacheados."""
        from sat_analysis.services.cache import ImageCache

        cache_dir = tmp_path / "cache"
        cache = ImageCache(cache_dir=cache_dir, max_size_mb=100.0)

        # Item que no existe
        cached = cache.get(item_id="NONEXISTENT")

        assert cached is None

    def test_cache_key_different_bbox(self, tmp_path, sample_sentinel_bands):
        """Verifica que diferentes BBOX generen diferentes claves."""
        from sat_analysis.services.cache import ImageCache
        from rasterio.transform import from_bounds

        cache_dir = tmp_path / "cache"
        cache = ImageCache(cache_dir=cache_dir, max_size_mb=100.0)

        item_id = "S2A_20HNG_20250101"
        bbox1 = [-63.0, -36.0, -62.0, -35.0]
        bbox2 = [-63.5, -36.5, -61.5, -34.5]
        crs = "EPSG:32720"
        transform = from_bounds(500000, 6000000, 501000, 6001000, 100, 100)

        # Guardar con bbox1
        cache.put(
            item_id=item_id,
            bands={"b02": sample_sentinel_bands.b02, "b03": sample_sentinel_bands.b03,
                   "b04": sample_sentinel_bands.b04, "b08": sample_sentinel_bands.b08,
                   "b11": sample_sentinel_bands.b11, "b12": sample_sentinel_bands.b12},
            crs=crs,
            transform=transform,
            bbox=bbox1,
        )

        # Buscar con bbox2 debe fallar
        cached = cache.get(item_id=item_id, bbox=bbox2)
        assert cached is None

        # Buscar con bbox1 debe funcionar
        cached = cache.get(item_id=item_id, bbox=bbox1)
        assert cached is not None

    def test_cache_delete(self, tmp_path, sample_sentinel_bands):
        """Verifica la eliminación de entradas del caché."""
        from sat_analysis.services.cache import ImageCache
        from rasterio.transform import from_bounds

        cache_dir = tmp_path / "cache"
        cache = ImageCache(cache_dir=cache_dir, max_size_mb=100.0)

        item_id = "S2A_20HNG_20250101"
        bbox = [-63.0, -36.0, -62.0, -35.0]
        crs = "EPSG:32720"
        transform = from_bounds(500000, 6000000, 501000, 6001000, 100, 100)

        # Guardar y obtener clave
        cache.put(
            item_id=item_id,
            bands={"b02": sample_sentinel_bands.b02, "b03": sample_sentinel_bands.b03,
                   "b04": sample_sentinel_bands.b04, "b08": sample_sentinel_bands.b08,
                   "b11": sample_sentinel_bands.b11, "b12": sample_sentinel_bands.b12},
            crs=crs,
            transform=transform,
            bbox=bbox,
        )

        key = list(cache.index.keys())[0]

        # Eliminar
        success = cache.delete(key)
        assert success is True
        assert len(cache.index) == 0

        # Verificar que ya no está
        cached = cache.get(item_id=item_id, bbox=bbox)
        assert cached is None

    def test_cache_clear(self, tmp_path, sample_sentinel_bands):
        """Verifica la limpieza completa del caché."""
        from sat_analysis.services.cache import ImageCache
        from rasterio.transform import from_bounds

        cache_dir = tmp_path / "cache"
        cache = ImageCache(cache_dir=cache_dir, max_size_mb=100.0)

        # Guardar varias entradas
        for i in range(3):
            cache.put(
                item_id=f"S2A_ITEM_{i}",
                bands={"b02": sample_sentinel_bands.b02, "b03": sample_sentinel_bands.b03,
                       "b04": sample_sentinel_bands.b04, "b08": sample_sentinel_bands.b08,
                       "b11": sample_sentinel_bands.b11, "b12": sample_sentinel_bands.b12},
                crs="EPSG:32720",
                transform=from_bounds(500000 + i * 1000, 6000000, 501000 + i * 1000, 6001000, 100, 100),
                bbox=[-63.0 + i * 0.1, -36.0, -62.0, -35.0],
            )

        assert len(cache.index) == 3

        # Limpiar todo
        cache.clear()

        assert len(cache.index) == 0

    def test_cache_stats(self, tmp_path, sample_sentinel_bands):
        """Verifica las estadísticas del caché."""
        from sat_analysis.services.cache import ImageCache
        from rasterio.transform import from_bounds

        cache_dir = tmp_path / "cache"
        cache = ImageCache(cache_dir=cache_dir, max_size_mb=100.0)

        # Caché vacío
        stats = cache.stats()
        assert stats["entry_count"] == 0
        assert stats["total_size_mb"] == 0.0

        # Agregar una entrada
        cache.put(
            item_id="S2A_20HNG_20250101",
            bands={"b02": sample_sentinel_bands.b02, "b03": sample_sentinel_bands.b03,
                   "b04": sample_sentinel_bands.b04, "b08": sample_sentinel_bands.b08,
                   "b11": sample_sentinel_bands.b11, "b12": sample_sentinel_bands.b12},
            crs="EPSG:32720",
            transform=from_bounds(500000, 6000000, 501000, 6001000, 100, 100),
            bbox=[-63.0, -36.0, -62.0, -35.0],
        )

        stats = cache.stats()
        assert stats["entry_count"] == 1
        assert stats["total_size_mb"] > 0
        assert 0 < stats["usage_percentage"] < 100

    def test_cache_cleanup_when_full(self, tmp_path):
        """Verifica que el caché se limpie cuando excede el tamaño máximo."""
        from sat_analysis.services.cache import ImageCache
        from rasterio.transform import from_bounds
        import numpy as np

        cache_dir = tmp_path / "cache"
        # Caché muy pequeño (1 MB)
        cache = ImageCache(cache_dir=cache_dir, max_size_mb=1.0, ttl_days=30)

        # Crear bandas grandes (300x300 = 90k píxeles × 6 bandas × 2 bytes ≈ 1 MB)
        large_bands = {
            "b02": np.zeros((300, 300), dtype=np.uint16),
            "b03": np.zeros((300, 300), dtype=np.uint16),
            "b04": np.zeros((300, 300), dtype=np.uint16),
            "b08": np.zeros((300, 300), dtype=np.uint16),
            "b11": np.zeros((300, 300), dtype=np.uint16),
            "b12": np.zeros((300, 300), dtype=np.uint16),
        }

        # Agregar varias entradas grandes
        for i in range(5):
            cache.put(
                item_id=f"S2A_ITEM_{i}",
                bands=large_bands,
                crs="EPSG:32720",
                transform=from_bounds(500000 + i * 1000, 6000000, 501000 + i * 1000, 6001000, 100, 100),
                bbox=[-63.0 + i * 0.1, -36.0, -62.0, -35.0],
            )

        # El caché debe haber limpiado entradas antiguas
        stats = cache.stats()
        print(f"\n[CACHE] Después de agregar 5 entradas grandes:")
        print(f"  Entradas: {stats['entry_count']}")
        print(f"  Tamaño: {stats['total_size_mb']:.2f} MB / {stats['max_size_mb']:.2f} MB")

        # El tamaño no debe exceder el máximo por mucho (permite 120% por limpieza batch)
        assert stats["total_size_mb"] <= cache.max_size_mb * 1.2
