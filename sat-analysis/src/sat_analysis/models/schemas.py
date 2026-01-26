"""
Esquemas de datos para el sistema sat-analysis.

Define modelos Pydantic para validación de datos de entrada y salida.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any


class ParcelData(BaseModel):
    """Datos de una parcela catastral."""

    partida: str
    bbox: list[float] = Field(description="[min_lon, min_lat, max_lon, max_lat]")
    area_approx_hectares: float | None = None
    geometry: dict[str, Any] | None = None


class ImageResult(BaseModel):
    """Resultado del análisis de una imagen."""

    date: str
    water_ha: float = Field(description="Área de agua en hectáreas")
    wetland_ha: float = Field(description="Área de humedal en hectáreas")
    vegetation_ha: float = Field(description="Área de vegetación en hectáreas")
    other_ha: float = Field(default=0.0, description="Área de otros en hectáreas")
    cloud_cover: float | None = None


class AnalysisResult(BaseModel):
    """Resultado completo del análisis de una parcela."""

    partida: str
    bbox: list[float]
    total_area_hectares: float
    date_range: str
    images_analyzed: int
    results: list[ImageResult]
    summary: dict[str, float] | None = None


class AnalysisRequest(BaseModel):
    """Request para análisis de parcela."""

    partida: str
    years: int = Field(default=2, ge=1, le=10)
    max_cloud_cover: int = Field(default=20, ge=0, le=100)
    max_images: int = Field(default=10, ge=1, le=50)
