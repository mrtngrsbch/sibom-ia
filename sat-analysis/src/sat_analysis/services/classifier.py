"""
Clasificador de píxeles para detección de agua, humedales y vegetación.

Implementa cálculo de índices espectrales (NDWI, NDVI, NDMI, MNDWI, NDSI, SI)
y clasificación basada en umbrales para imágenes Sentinel-2.
"""
import numpy as np
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SpectralIndices:
    """Índices espectrales calculados."""

    ndwi: np.ndarray  # Normalized Difference Water Index
    mndwi: np.ndarray  # Modified NDWI
    ndvi: np.ndarray  # Normalized Difference Vegetation Index
    ndmi: np.ndarray  # Normalized Difference Moisture Index
    ndsi: np.ndarray  # Normalized Difference Salinity Index (para detección de sal)
    salinity_index: np.ndarray  # Salinity Index (SWIR2 / (SWIR2 + NIR))


@dataclass
class ClassificationResult:
    """Resultado de la clasificación de píxeles."""

    classification: np.ndarray  # Array con clases: 0=Otros, 1=Agua, 2=Humedal, 3=Vegetación
    areas_hectares: dict[int, float]  # Área por clase en hectáreas
    pixel_count: dict[int, int]  # Cantidad de píxeles por clase


class PixelClassifier:
    """
    Clasificador de píxeles basado en índices espectrales.

    Implementa umbrales para clasificar píxeles en:
    - Agua (NDWI > 0.15 OR MNDWI > 0.25)
    - Humedal (NDVI > 0.35 AND NDMI > 0.10 AND NDWI > -0.6)
    - Vegetación (NDVI > 0.5 AND NDMI < 0.2)
    - Otros (resto)

    Nota: Los umbrales están ajustados para humedales de Argentina,
    donde la vegetación húmeda tiene NDWI típicamente negativo.
    """

    # Nombres de clases para output
    CLASS_NAMES = {
        0: "Otros",
        1: "Agua",
        2: "Humedal",
        3: "Vegetación",
    }

    # Colores para visualización
    CLASS_COLORS = {
        0: (128, 128, 128),  # Gris
        1: (0, 0, 255),      # Azul
        2: (0, 128, 0),      # Verde oscuro
        3: (0, 255, 0),      # Verde claro
    }

    def __init__(
        self,
        water_ndwi_threshold: float = 0.15,  # Reducido de 0.2
        water_mndwi_threshold: float = 0.25,  # Reducido de 0.3
        wetland_ndvi_threshold: float = 0.35,  # Reducido de 0.4
        wetland_ndmi_threshold: float = 0.10,  # Reducido de 0.15
        wetland_ndwi_threshold: float = -0.6,  # Cambiado de -0.1 a -0.6 (no excluir vegetación húmeda)
        vegetation_ndvi_threshold: float = 0.5,
        vegetation_ndmi_threshold: float = 0.2,
    ):
        """
        Inicializa el clasificador con umbrales personalizados.

        Args:
            water_ndwi_threshold: Umbral NDWI para agua
            water_mndwi_threshold: Umbral MNDWI para agua turbia
            wetland_ndvi_threshold: Umbral NDVI para humedal
            wetland_ndmi_threshold: Umbral NDMI para humedal
            wetland_ndwi_threshold: Umbral NDWI para humedal
            vegetation_ndvi_threshold: Umbral NDVI para vegetación
            vegetation_ndmi_threshold: Umbral NDMI máximo para vegetación seca
        """
        self.water_ndwi_threshold = water_ndwi_threshold
        self.water_mndwi_threshold = water_mndwi_threshold
        self.wetland_ndvi_threshold = wetland_ndvi_threshold
        self.wetland_ndmi_threshold = wetland_ndmi_threshold
        self.wetland_ndwi_threshold = wetland_ndwi_threshold
        self.vegetation_ndvi_threshold = vegetation_ndvi_threshold
        self.vegetation_ndmi_threshold = vegetation_ndmi_threshold

    def calculate_indices(
        self,
        b02: np.ndarray,
        b03: np.ndarray,
        b04: np.ndarray,
        b08: np.ndarray,
        b11: np.ndarray,
        b12: np.ndarray | None = None,
    ) -> SpectralIndices:
        """
        Calcula índices espectrales desde bandas Sentinel-2.

        Args:
            b02: Banda Blue (490 nm)
            b03: Banda Green (560 nm)
            b04: Banda Red (665 nm)
            b08: Banda NIR (842 nm)
            b11: Banda SWIR1 (1610 nm)
            b12: Banda SWIR2 (2190 nm) - opcional, para índices de salinidad

        Returns:
            SpectralIndices con los índices calculados

        Nota:
            Asume que las bandas están en reflectancia 0-1.
            Se usa epsilon=1e-8 para evitar división por cero.

        Referencias:
            - NDWI: McFeeters (1996)
            - MNDWI: Xu (2006)
            - NDSI: Normalized Difference Salinity Index para suelos salinos
            - SI: Salinity Index usando SWIR2
        """
        eps = 1e-8

        # NDWI - McFeeters (1996) para agua
        # (Green - NIR) / (Green + NIR)
        ndwi = (b03 - b08) / (b03 + b08 + eps)

        # MNDWI - Modified NDWI (Xu 2006) para agua turbia
        # (Green - SWIR1) / (Green + SWIR1)
        mndwi = (b03 - b11) / (b03 + b11 + eps)

        # NDVI - Vegetación
        # (NIR - Red) / (NIR + Red)
        ndvi = (b08 - b04) / (b08 + b04 + eps)

        # NDMI - Humedad en vegetación
        # (NIR - SWIR1) / (NIR + SWIR1)
        ndmi = (b08 - b11) / (b08 + b11 + eps)

        # Índices de salinidad (requieren SWIR2 / B12)
        if b12 is not None:
            # NDSI - Normalized Difference Salinity Index
            # (Green - SWIR2) / (Green + SWIR2)
            # Los suelos salinos tienen reflectancia alta en SWIR2
            ndsi = (b03 - b12) / (b03 + b12 + eps)

            # SI - Salinity Index
            # SWIR2 / (SWIR2 + NIR)
            # Valores altos indican posible salinización
            salinity_index = b12 / (b12 + b08 + eps)
        else:
            # Si no hay B12, retornar arrays vacíos con shape correcto
            ndsi = np.zeros_like(ndwi)
            salinity_index = np.zeros_like(ndwi)

        return SpectralIndices(
            ndwi=ndwi,
            mndwi=mndwi,
            ndvi=ndvi,
            ndmi=ndmi,
            ndsi=ndsi,
            salinity_index=salinity_index,
        )

    def classify(self, indices: SpectralIndices) -> ClassificationResult:
        """
        Clasifica píxeles basado en índices espectrales.

        Args:
            indices: SpectralIndices calculados

        Returns:
            ClassificationResult con array de clases y áreas
        """
        # Inicializar array de clasificación (0 = Otros)
        shape = indices.ndwi.shape
        classification = np.zeros(shape, dtype=np.uint8)

        # Máscara de agua (prioridad alta)
        # Agua abierta: NDWI alto
        # Agua turbia: MNDWI alto
        water_mask = (indices.ndwi > self.water_ndwi_threshold) | (
            indices.mndwi > self.water_mndwi_threshold
        )
        classification[water_mask] = 1

        # Máscara de humedal (vegetación húmeda, no agua)
        # NDVI alto (vegetación)
        # NDMI alto (humedad)
        # NDWI > umbral negativo (algo de agua en el entorno)
        wetland_mask = (
            (indices.ndvi > self.wetland_ndvi_threshold)
            & (indices.ndmi > self.wetland_ndmi_threshold)
            & (indices.ndwi > self.wetland_ndwi_threshold)
            & (~water_mask)
        )
        classification[wetland_mask] = 2

        # Máscara de vegetación seca/sana
        # NDVI alto pero NDMI bajo (no es humedal)
        veg_mask = (
            (indices.ndvi > self.vegetation_ndvi_threshold)
            & (indices.ndmi < self.vegetation_ndmi_threshold)
            & (~water_mask)
            & (~wetland_mask)
        )
        classification[veg_mask] = 3

        # El resto queda como 0 (Otros)

        return ClassificationResult(
            classification=classification,
            areas_hectares={},  # Se calcula con pixel_area
            pixel_count={},
        )

    def calculate_areas(
        self,
        classification: np.ndarray,
        pixel_area_m2: float = 100.0,
    ) -> dict[int, float]:
        """
        Calcula el área por clase en hectáreas.

        Args:
            classification: Array de clases
            pixel_area_m2: Área de un píxel en m² (100 m² para Sentinel-2 10m)

        Returns:
            Dict con clase -> área en hectáreas
        """
        unique, counts = np.unique(classification, return_counts=True)

        areas = {}
        for label, count in zip(unique, counts):
            # m² a hectáreas (dividir por 10000)
            areas[label] = (count * pixel_area_m2) / 10000

        return areas

    def classify_with_areas(
        self,
        indices: SpectralIndices,
        pixel_area_m2: float = 100.0,
    ) -> ClassificationResult:
        """
        Clasifica y calcula áreas en un solo paso.

        Args:
            indices: SpectralIndices calculados
            pixel_area_m2: Área de un píxel en m²

        Returns:
            ClassificationResult completo
        """
        result = self.classify(indices)

        # Calcular áreas
        result.areas_hectares = self.calculate_areas(
            result.classification, pixel_area_m2
        )

        # Calcular conteo de píxeles
        unique, counts = np.unique(result.classification, return_counts=True)
        result.pixel_count = dict(zip(unique.tolist(), counts.tolist()))

        return result

    def apply_mask(
        self,
        classification: np.ndarray,
        areas_hectares: dict[int, float],
        mask: np.ndarray,
        pixel_area_m2: float = 100.0,
    ) -> ClassificationResult:
        """
        Aplica máscara de parcela al resultado de clasificación.

        Píxeles fuera de la máscara se excluyen del análisis.
        Solo se recalculan áreas usando píxeles dentro de la parcela.

        Args:
            classification: Array de clases
            areas_hectares: Áreas por clase (se ignoran, se recalculan)
            mask: Boolean array donde True = dentro de parcela
            pixel_area_m2: Área de un píxel en m²

        Returns:
            ClassificationResult con máscara aplicada

        Nota:
            Píxeles fuera de la máscara se marcan como clase 255 (excluido).
            Este valor especial se usa para distinguir píxeles excluidos de la clase 0 (Otros).
        """
        # Crear una copia y marcar píxeles fuera como clase 255 (excluido)
        masked_classification = classification.copy()
        masked_classification[~mask] = 255  # Valor especial para "excluido"

        # Calcular áreas solo con píxeles dentro de la máscara
        unique, counts = np.unique(masked_classification, return_counts=True)
        new_areas = {}

        for label, count in zip(unique, counts):
            if label == 255:  # Excluido, no contar
                continue
            # m² a hectáreas (dividir por 10000)
            new_areas[label] = (count * pixel_area_m2) / 10000

        # Calcular nuevo conteo de píxeles (solo dentro de máscara)
        unique_valid, counts_valid = np.unique(
            masked_classification[mask], return_counts=True
        )
        new_counts = dict(zip(unique_valid.tolist(), counts_valid.tolist()))

        return ClassificationResult(
            classification=masked_classification,
            areas_hectares=new_areas,
            pixel_count=new_counts,
        )
