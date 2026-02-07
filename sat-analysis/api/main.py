"""
FastAPI backend para análisis satelital.

Reemplaza la interfaz Gradio con una API REST moderna.
"""
import asyncio
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from sat_analysis.config import get_settings

from .models import (
    AnalyzeRequest,
    AnalyzeResponse,
    TaskCreateResponse,
    TaskStatus,
    PartidoInfo,
    PartidosList,
    HealthResponse,
)
from .tasks import task_store, run_analysis_task, load_partidos

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Sat-Analysis API",
    description="Análisis satelital de parcelas catastrales ARBA usando imágenes Sentinel-2",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurar CORS para Next.js frontend
# Leer orígenes permitidos desde variable de entorno o usar defaults
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001,https://sibom-assistant.vercel.app"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorio de salida para imágenes
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/app/data/web_output"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Obtener versión del paquete
try:
    from importlib.metadata import version
    __version__ = version("sat-analysis")
except Exception:
    __version__ = "2.0.0"


@app.get("/", tags=["Root"])
async def root():
    """Endpoint raíz con información básica."""
    return {
        "service": "Sat-Analysis API",
        "version": __version__,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint para monitoreo.

    Retorna el estado del servicio y su versión.
    """
    return HealthResponse(
        status="healthy",
        service="sat-analysis-api",
        version=__version__,
    )


@app.get("/api/partidos", response_model=PartidosList, tags=["ARBA"])
async def get_partidos():
    """
    Obtiene la lista de partidos ARBA disponibles.

    Retorna un diccionario con códigos y nombres de partidos.
    """
    partidos_dict = load_partidos()

    partidos = [
        PartidoInfo(codigo=codigo, nombre=nombre)
        for codigo, nombre in sorted(partidos_dict.items(), key=lambda x: x[1])
    ]

    return PartidosList(partidos=partidos)


@app.post("/api/analyze", response_model=TaskCreateResponse, tags=["Analysis"])
async def create_analysis(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks
):
    """
    Inicia un análisis de parcela catastral en background.

    El análisis es asíncrono y retorna inmediatamente con un task_id.
    Usa GET /api/analyze/{task_id} para consultar el estado y resultados.

    Args:
        request: Parámetros de análisis (partida, years, samples_per_year, max_clouds)
        background_tasks: FastAPI BackgroundTasks para ejecutar en segundo plano

    Returns:
        TaskCreateResponse con task_id único y status inicial
    """
    # Validar partida
    if not request.partida or not request.partida.strip():
        raise HTTPException(status_code=400, detail="La partida no puede estar vacía")

    # Generar task_id único
    task_id = str(uuid.uuid4())

    # Inicializar respuesta de tarea
    analyze_response = AnalyzeResponse(
        task_id=task_id,
        partida=request.partida,
        status=TaskStatus.PENDING,
        progress=0.0,
        message="Análisis iniciado, en cola para procesamiento",
        total_images=0,
    )

    # Guardar en store
    await task_store.set(task_id, analyze_response)

    # Extraer código de partido de la partida (si está incluida)
    # Formato esperado: codigo_partido + partida (ej: "002004606")
    partida_input = request.partida.strip()

    # Si la partida tiene código incluido (9+ dígitos)
    if len(partida_input) >= 9 and partida_input.isdigit():
        codigo_partido = partida_input[:3]
        partida_individual = partida_input[3:]
    else:
        # Asumir que es solo la partida individual
        # Usar código por defecto o intentar extraer del formato
        codigo_partido = "002"  # Default Alberti
        partida_individual = partida_input

    # Agregar tarea de fondo
    background_tasks.add_task(
        run_analysis_task,
        task_id,
        partida_individual,
        codigo_partido,
        request.years,
        request.samples_per_year,
        request.max_clouds,
        OUTPUT_DIR,
    )

    logger.info(f"Análisis iniciado: task_id={task_id}, partida={request.partida}")

    return TaskCreateResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        message="Análisis iniciado correctamente",
    )


@app.get("/api/analyze/{task_id}", response_model=AnalyzeResponse, tags=["Analysis"])
async def get_analysis_status(task_id: str):
    """
    Obtiene el estado y resultados de un análisis.

    Usa este endpoint para hacer polling mientras la tarea está en procesamiento.
    Cuando status='completed', los resultados estarán disponibles.

    Args:
        task_id: ID de la tarea retornado por POST /api/analyze

    Returns:
        AnalyzeResponse con estado actual, progreso y resultados (si están listos)

    Raises:
        HTTPException 404: Si el task_id no existe
    """
    response = await task_store.get(task_id)

    if response is None:
        raise HTTPException(status_code=404, detail=f"Tarea {task_id} no encontrada")

    return response


@app.get("/api/tasks", tags=["Admin"])
async def list_tasks():
    """
    Lista todas las tareas de análisis en memoria.

    NOTA: Este endpoint es para desarrollo/debug. Las tareas se pierden al reiniciar.
    """
    tasks = await task_store.tasks if hasattr(task_store, 'tasks') else {}
    return {
        "total": len(tasks),
        "tasks": [
            {
                "task_id": task_id,
                "partida": task.partida,
                "status": task.status,
                "progress": task.progress,
            }
            for task_id, task in tasks.items()
        ]
    }


@app.delete("/api/tasks/{task_id}", tags=["Admin"])
async def delete_task(task_id: str):
    """
    Elimina una tarea de la memoria.

    Útil para limpiar tareas completadas o fallidas.
    """
    response = await task_store.get(task_id)

    if response is None:
        raise HTTPException(status_code=404, detail=f"Tarea {task_id} no encontrada")

    # Eliminar del store
    if hasattr(task_store, '_lock'):
        async with task_store._lock:
            if task_id in task_store.tasks:
                del task_store.tasks[task_id]

    return {"message": f"Tarea {task_id} eliminada"}


# Startup event
@app.on_event("startup")
async def startup_event():
    """Event handler al iniciar la aplicación."""
    logger.info("Iniciando Sat-Analysis API v%s", __version__)
    logger.info("Directorio de salida: %s", OUTPUT_DIR)

    settings = get_settings()
    logger.info("Umbrales de clasificación:")
    logger.info("  - Agua (NDWI): %.2f", settings.water_ndwi_threshold)
    logger.info("  - Agua turbia (MNDWI): %.2f", settings.water_mndwi_threshold)
    logger.info("  - Humedal (NDVI): %.2f", settings.wetland_ndvi_threshold)
    logger.info("  - Humedal (NDMI): %.2f", settings.wetland_ndmi_threshold)
    logger.info("  - Vegetación (NDVI): %.2f", settings.vegetation_ndvi_threshold)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Event handler al apagar la aplicación."""
    logger.info("Apagando Sat-Analysis API")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
    )
