"""
Esquemas de datos para el sistema sat-analysis.

Define modelos Pydantic para validación de datos de entrada y salida.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any


class PartidaARBA(BaseModel):
    """Partida catastral ARBA parseada en sus componentes."""

    codigo_partido: str = Field(description="Código de partido (3 dígitos)")
    nombre_partido: str = Field(description="Nombre del partido")
    partida_individual: str = Field(description="Partida individual (6 dígitos)")
    verificador: str | None = Field(default=None, description="Dígito verificador")
    formato_completo: str = Field(description="Formato normalizado para display")

    @property
    def partida_completa(self) -> str:
        """Retorna partida completa sin verificador (9 dígitos)."""
        return f"{self.codigo_partido}{self.partida_individual}"

    @property
    def cql_filter(self) -> str:
        """Retorna filtro CQL para consultar ARBA WFS."""
        return f"partido='{self.codigo_partido}' AND pda='{self.partida_individual}'"


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
