"""
Modelos Pydantic para la API FastAPI de sat-analysis.

Extiende los modelos del core con campos específicos para la API REST.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class TaskStatus(str, Enum):
    """Estados posibles de una tarea de análisis."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalyzeRequest(BaseModel):
    """Request para iniciar análisis de parcela."""
    partida: str = Field(
        ...,
        description="Partida catastral (ej: '002004606' o '4606')",
        min_length=3,
        max_length=20
    )
    years: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Años de histórico a analizar"
    )
    samples_per_year: int = Field(
        default=4,
        ge=1,
        le=12,
        description="Imágenes por año con distribución uniforme"
    )
    max_clouds: int = Field(
        default=20,
        ge=0,
        le=100,
        description="Máximo porcentaje de nubes"
    )


class ImageUrls(BaseModel):
    """URLs de imágenes generadas para una fecha."""
    clasificacion: Optional[str] = Field(None, description="Imagen de clasificación de uso de suelo")
    ndwi: Optional[str] = Field(None, description="Índice NDWI")
    ndvi: Optional[str] = Field(None, description="Índice NDVI")
    ndmi: Optional[str] = Field(None, description="Índice NDMI")
    mndwi: Optional[str] = Field(None, description="Índice MNDWI")
    ndsi: Optional[str] = Field(None, description="Índice NDSI")
    swir2_nir: Optional[str] = Field(None, description="Ratio SWIR2/NIR")
    rgb: Optional[str] = Field(None, description="Imagen color real (RGB)")


class ImageResultDTO(BaseModel):
    """Resultado del análisis de una imagen (DTO para API)."""
    date: str = Field(..., description="Fecha de la imagen ISO 8601")
    water_ha: float = Field(..., description="Área de agua en hectáreas")
    wetland_ha: float = Field(..., description="Área de humedal en hectáreas")
    vegetation_ha: float = Field(..., description="Área de vegetación en hectáreas")
    other_ha: float = Field(default=0.0, description="Área de otros en hectáreas")
    cloud_cover: Optional[float] = Field(None, description="Porcentaje de nubes")
    images: Optional[ImageUrls] = Field(None, description="URLs de imágenes generadas")

    class Config:
        """Configuración Pydantic."""
        json_encoders = {
            float: lambda v: round(v, 2)
        }


class AnalysisSummary(BaseModel):
    """Resumen del análisis de parcela."""
    partida: str
    total_area_ha: Optional[float] = None
    date_range: str
    images_analyzed: int
    max_water_ha: float
    max_wetland_ha: float
    avg_water_ha: float
    avg_wetland_ha: float
    max_affected_date: str
    max_affected_area_ha: float
    trend_water: str  # "up", "down", "stable"
    trend_wetland: str  # "up", "down", "stable"


class AnalyzeResponse(BaseModel):
    """Respuesta de análisis para polling."""
    task_id: str
    partida: str
    status: TaskStatus
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    message: str = Field(default="")
    total_images: int = Field(default=0)
    results: Optional[List[ImageResultDTO]] = None
    summary: Optional[AnalysisSummary] = None
    error: Optional[str] = None


class PartidoInfo(BaseModel):
    """Información de un partido ARBA."""
    codigo: str
    nombre: str


class PartidosList(BaseModel):
    """Lista de partidos ARBA disponibles."""
    partidos: List[PartidoInfo]


class HealthResponse(BaseModel):
    """Respuesta de health check."""
    status: str
    service: str
    version: str


class TaskCreateResponse(BaseModel):
    """Respuesta al crear una tarea de análisis."""
    task_id: str
    status: TaskStatus
    message: str = "Análisis iniciado correctamente"
