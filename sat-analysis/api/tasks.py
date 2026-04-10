"""
Background tasks para análisis satelital asíncrono.

Este módulo contiene la lógica de análisis adaptada desde app.py
para ejecutarse en segundo plano con FastAPI BackgroundTasks.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from sat_analysis.services import ArbaService, StacService, PixelClassifier, PartidaParser
from sat_analysis.services.arba import ArbaError
from sat_analysis.services.stac import StacError, get_pixel_area_m2
from sat_analysis.models.schemas import ImageResult
from sat_analysis.config import get_settings

from .models import (
    AnalysisSummary,
    AnalyzeResponse,
    ImageResultDTO,
    ImageUrls,
    SensorType,
    TaskStatus,
)

logger = logging.getLogger(__name__)


class TaskStore:
    """Almacenamiento en memoria para tareas de análisis."""

    def __init__(self):
        self.tasks: dict[str, AnalyzeResponse] = {}
        self._lock = asyncio.Lock()

    async def get(self, task_id: str) -> Optional[AnalyzeResponse]:
        """Obtiene una tarea por ID."""
        async with self._lock:
            return self.tasks.get(task_id)

    async def set(self, task_id: str, response: AnalyzeResponse) -> None:
        """Guarda o actualiza una tarea."""
        async with self._lock:
            self.tasks[task_id] = response

    async def update_progress(
        self,
        task_id: str,
        progress: float,
        message: str = "",
        status: Optional[TaskStatus] = None
    ) -> None:
        """Actualiza el progreso de una tarea."""
        async with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id].progress = progress
                if message:
                    self.tasks[task_id].message = message
                if status:
                    self.tasks[task_id].status = status


# Singleton store
task_store = TaskStore()


async def run_analysis_task(
    task_id: str,
    partida: str,
    codigo_partido: str,
    years: int,
    samples_per_year: int,
    max_clouds: int,
    output_dir: Path
) -> None:
    """
    Ejecuta el análisis de parcela en background.

    Args:
        task_id: ID único de la tarea
        partida: Número de partida individual (ej: "4606")
        codigo_partido: Código de partido ARBA (ej: "002")
        years: Años de histórico
        samples_per_year: Imágenes por año
        max_clouds: Máximo % de nubes
        output_dir: Directorio para guardar imágenes
    """
    try:
        await task_store.update_progress(task_id, 0.0, "Iniciando análisis...", TaskStatus.PROCESSING)

        # 1. Parsear partida
        try:
            parser = PartidaParser()
            partida_completa = f"{codigo_partido}{partida.zfill(6)}"
            partida_arba = parser.parse(partida_completa)
        except ValueError as e:
            await task_store.update_progress(task_id, 0.0, f"Error en partida: {e}", TaskStatus.FAILED)
            response = await task_store.get(task_id)
            if response:
                response.error = str(e)
            return

        await task_store.update_progress(task_id, 0.1, f"Consultando parcela {partida_arba.formato_completo}...")

        # 2. Obtener geometría de parcela
        parcel_bbox = None
        total_area_ha = None
        parcel_geometry = None

        try:
            arba = ArbaService()
            parcel = arba.get_parcel_geometry(partida_arba)

            if parcel is None:
                await task_store.update_progress(
                    task_id, 0.0, f"Partida {partida_arba.formato_completo} no encontrada en ARBA", TaskStatus.FAILED
                )
                response = await task_store.get(task_id)
                if response:
                    response.error = "Partida no encontrada en ARBA"
                return

            parcel_bbox = parcel.bbox
            parcel_geometry = parcel.geometry
            total_area_ha = parcel.area_approx_hectares

        except ArbaError as e:
            await task_store.update_progress(task_id, 0.0, f"Error consultando ARBA: {e}", TaskStatus.FAILED)
            response = await task_store.get(task_id)
            if response:
                response.error = f"Error ARBA: {e}"
            return

        await task_store.update_progress(task_id, 0.2, "Buscando imágenes satelitales...")

        # 3. Buscar imágenes
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        date_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"

        try:
            stac = StacService()
            items = stac.search_sentinel_sampled(
                bbox=parcel_bbox,
                date_range=date_range,
                max_clouds=float(max_clouds),
                samples_per_year=samples_per_year,
                start_date=start_date,
                end_date=end_date,
            )

            if not items:
                await task_store.update_progress(
                    task_id, 0.0, "No se encontraron imágenes. Pruebe con más años o menos restricción de nubes", TaskStatus.FAILED
                )
                response = await task_store.get(task_id)
                if response:
                    response.error = "No se encontraron imágenes"
                return

            await task_store.update_progress(task_id, 0.25, f"Se encontraron {len(items)} imágenes")

        except StacError as e:
            await task_store.update_progress(task_id, 0.0, f"Error buscando imágenes: {e}", TaskStatus.FAILED)
            response = await task_store.get(task_id)
            if response:
                response.error = f"Error STAC: {e}"
            return

        # 4. Configurar clasificador
        settings = get_settings()
        classifier = PixelClassifier(
            water_ndwi_threshold=settings.water_ndwi_threshold,
            water_mndwi_threshold=settings.water_mndwi_threshold,
            wetland_ndvi_threshold=settings.wetland_ndvi_threshold,
            wetland_ndmi_threshold=settings.wetland_ndmi_threshold,
            wetland_ndwi_threshold=settings.wetland_ndwi_threshold,
            vegetation_ndvi_threshold=settings.vegetation_ndvi_threshold,
            vegetation_ndmi_threshold=settings.vegetation_ndmi_threshold,
        )

        results = []
        image_urls_list = []
        total_items = len(items)
        partida_clean = partida.replace('coords:', 'c').replace(':', '_')

        # 5. Procesar imágenes
        for i, item in enumerate(items):
            progress_val = 0.3 + (0.6 * (i + 1) / total_items)
            await task_store.update_progress(
                task_id,
                progress_val,
                f"Procesando imagen {i+1}/{total_items}..."
            )

            try:
                bands = stac.download_bands(item, bbox=parcel_bbox, geometry=None)
                pixel_area = get_pixel_area_m2(bands.transform, bands.crs)

                indices = classifier.calculate_indices(
                    b02=bands.b02, b03=bands.b03, b04=bands.b04,
                    b08=bands.b08, b11=bands.b11, b12=bands.b12,
                )

                result = classifier.classify_with_areas(indices, pixel_area_m2=pixel_area)

                # Crear y aplicar máscara específica para esta imagen
                parcel_mask = None
                if parcel_geometry is not None:
                    parcel_mask = stac.create_parcel_mask(
                        shape=bands.b02.shape,
                        geometry=parcel_geometry,
                        bbox=parcel_bbox,
                        image_crs=bands.crs,
                        transform=bands.transform
                    )
                    result = classifier.apply_mask(
                        classification=result.classification,
                        areas_hectares=result.areas_hectares,
                        mask=parcel_mask,
                        pixel_area_m2=pixel_area
                    )

                water_ha = result.areas_hectares.get(1, 0)
                wetland_ha = result.areas_hectares.get(2, 0)
                vegetation_ha = result.areas_hectares.get(3, 0)
                other_ha = result.areas_hectares.get(0, 0)

                # Generar y guardar imágenes de visualización
                date_str = item.datetime[:10].replace('-', '')
                img_urls = _save_per_image_visualizations(
                    bands=bands,
                    indices=indices,
                    classification=result.classification,
                    parcel_mask=parcel_mask,
                    partida_clean=partida_clean,
                    date_str=date_str,
                    output_dir=output_dir,
                )

                results.append(ImageResult(
                    date=item.datetime,
                    water_ha=round(water_ha, 2),
                    wetland_ha=round(wetland_ha, 2),
                    vegetation_ha=round(vegetation_ha, 2),
                    other_ha=round(other_ha, 2),
                    cloud_cover=item.cloud_cover,
                ))
                image_urls_list.append(img_urls)

            except StacError as e:
                logger.warning(f"Error procesando imagen {i}: {e}")
                image_urls_list.append(None)
                continue

        if not results:
            await task_store.update_progress(task_id, 0.0, "Error procesando todas las imágenes", TaskStatus.FAILED)
            response = await task_store.get(task_id)
            if response:
                response.error = "Error procesando imágenes"
            return

        await task_store.update_progress(task_id, 0.95, "Generando resumen...")

        # 6. Calcular resumen estadístico
        summary = _calculate_summary(results, total_area_ha, date_range, partida, years, samples_per_year)

        # 7. Calcular diagnóstico profesional
        diagnostic = _calculate_diagnostic(results, summary)

        # 8. Guardar imágenes (opcional, para debug)
        await _save_indices_images_async(results, partida, output_dir)

        # 9. Actualizar tarea como completada
        response = await task_store.get(task_id)
        if response:
            response.status = TaskStatus.COMPLETED
            response.progress = 1.0
            response.message = "Análisis completado exitosamente"
            response.total_images = len(results)
            # Incluir las URLs de las imágenes en cada resultado
            response.results = [
                ImageResultDTO(
                    date=r.date,
                    water_ha=r.water_ha,
                    wetland_ha=r.wetland_ha,
                    vegetation_ha=r.vegetation_ha,
                    other_ha=r.other_ha,
                    cloud_cover=r.cloud_cover,
                    images=image_urls_list[i] if i < len(image_urls_list) else None,
                )
                for i, r in enumerate(results)
            ]
            response.summary = summary
            response.diagnostic = diagnostic

        await task_store.set(task_id, response)

    except Exception as e:
        logger.exception(f"Error en análisis {task_id}")
        await task_store.update_progress(task_id, 0.0, f"Error inesperado: {e}", TaskStatus.FAILED)
        response = await task_store.get(task_id)
        if response:
            response.error = str(e)


# Diagnóstico profesional automático
def _calculate_diagnostic(results: list, summary: 'AnalysisSummary') -> 'DiagnosticResult':
    """
    Diagnóstico de riesgo hídrico con algoritmo ponderado multi-métrica.

    Componentes:
      S1 (35%) — Exposición media: fracción promedio de área afectada (agua + humedal)
      S2 (30%) — Pico de exposición: fracción máxima en el peor evento registrado
      S3 (20%) — Frecuencia: % de imágenes con área afectada > 10 %
      S4 (15%) — Tendencia: pendiente de regresión lineal (positiva = empeoramiento)

    Escala de riesgo final:
      >= 75  → Bajo
      50–74  → Moderado
      30–49  → Elevado
      < 30   → Alto
    """
    if not results or not summary:
        return None

    from .models import DiagnosticResult, DiagnosticScore

    total_area = summary.total_area_ha or 1.0
    n = len(results)

    # ── 1. Fracción afectada (agua + humedal) por imagen ─────────────────
    affected = [(r.water_ha + r.wetland_ha) / total_area * 100 for r in results]
    avg_affected = sum(affected) / n
    max_affected = max(affected)

    # ── 2. Frecuencia de eventos significativos (> 10 % del área) ────────
    THRESHOLD = 10.0
    freq_pct = sum(1 for f in affected if f > THRESHOLD) / n * 100

    # ── 3. Tendencia por regresión lineal (pendiente en %·imagen⁻¹) ──────
    if n >= 3:
        xs = list(range(n))
        x_mean = (n - 1) / 2.0

        def _slope(vals: list) -> float:
            y_mean = sum(vals) / n
            num = sum((xs[i] - x_mean) * (vals[i] - y_mean) for i in range(n))
            den = sum((x - x_mean) ** 2 for x in xs)
            return num / den if den > 0 else 0.0

        water_slope = _slope([r.water_ha / total_area * 100 for r in results])
        wetland_slope = _slope([r.wetland_ha / total_area * 100 for r in results])
    else:
        water_slope = wetland_slope = 0.0

    # ── 4. Puntajes por componente (0 = crítico, 100 = sin riesgo) ───────
    S1 = max(0.0, 100.0 - avg_affected * 2.0)    # 50 % avg  → S1 = 0
    S2 = max(0.0, 100.0 - max_affected * 1.5)     # 67 % pico → S2 = 0
    S3 = max(0.0, 100.0 - freq_pct * 1.5)         # 67 % freq → S3 = 0
    combined_slope = water_slope + wetland_slope
    S4 = max(0.0, 100.0 - max(0.0, combined_slope) * 20.0)

    # ── 5. Score global ponderado ─────────────────────────────────────────
    overall = round(0.35 * S1 + 0.30 * S2 + 0.20 * S3 + 0.15 * S4, 1)

    # ── 6. Nivel de riesgo e interpretación ──────────────────────────────
    if overall >= 75:
        risk_level = "Bajo"
        interpretation = "Sin riesgo significativo de anegamiento/salinización."
    elif overall >= 50:
        risk_level = "Moderado"
        interpretation = "Riesgo moderado: se recomienda monitoreo periódico."
    elif overall >= 30:
        risk_level = "Elevado"
        interpretation = "Riesgo elevado: considerar medidas de drenaje o manejo hídrico."
    else:
        risk_level = "Alto"
        interpretation = "Riesgo alto: se recomienda intervención técnica urgente."

    def _trend_label(sl: float) -> str:
        if sl > 0.5:
            return "creciente ↑"
        if sl < -0.5:
            return "decreciente ↓"
        return "estable →"

    return DiagnosticResult(
        overall_score=overall,
        risk_level=risk_level,
        scores=[
            DiagnosticScore(
                name="Exposición media",
                value=round(avg_affected, 1),
                label="% área afectada (prom.)",
                interpretation="Fracción promedio de área con agua+humedal sobre el total de la parcela.",
                component_score=round(S1, 1),
            ),
            DiagnosticScore(
                name="Pico de exposición",
                value=round(max_affected, 1),
                label="% área en el peor evento",
                interpretation="Máxima fracción afectada registrada en el período analizado.",
                component_score=round(S2, 1),
            ),
            DiagnosticScore(
                name="Frecuencia de eventos",
                value=round(freq_pct, 1),
                label="% imágenes con >10 % área afectada",
                interpretation="Qué tan frecuentes son los eventos de anegamiento significativos.",
                component_score=round(S3, 1),
            ),
            DiagnosticScore(
                name="Tendencia temporal",
                value=round(combined_slope, 2),
                label="pendiente %·imagen⁻¹",
                interpretation=f"Agua: {_trend_label(water_slope)}, Humedal: {_trend_label(wetland_slope)}",
                component_score=round(S4, 1),
            ),
        ],
        interpretation=interpretation,
    )


def _calculate_summary(
    results: list[ImageResult],
    total_area_ha: Optional[float],
    date_range: str,
    partida: str,
    years: int,
    samples_per_year: int
) -> AnalysisSummary:
    """Calcula el resumen estadístico del análisis."""
    if not results:
        return AnalysisSummary(
            partida=partida,
            date_range=date_range,
            images_analyzed=0,
            max_water_ha=0,
            max_wetland_ha=0,
            avg_water_ha=0,
            avg_wetland_ha=0,
            max_affected_date="",
            max_affected_area_ha=0,
            trend_water="stable",
            trend_wetland="stable",
        )

    max_water = max(r.water_ha for r in results)
    max_wetland = max(r.wetland_ha for r in results)
    avg_water = sum(r.water_ha for r in results) / len(results)
    avg_wetland = sum(r.wetland_ha for r in results) / len(results)

    max_affected_result = max(results, key=lambda r: r.water_ha + r.wetland_ha)
    max_affected_date = max_affected_result.date[:10] if len(max_affected_result.date) > 10 else max_affected_result.date
    max_affected_area = max_affected_result.water_ha + max_affected_result.wetland_ha

    # Calcular tendencias
    if len(results) >= 2:
        first = results[0]
        last = results[-1]
        water_diff = last.water_ha - first.water_ha
        wetland_diff = last.wetland_ha - first.wetland_ha

        trend_water = "up" if water_diff > 1 else "down" if water_diff < -1 else "stable"
        trend_wetland = "up" if wetland_diff > 1 else "down" if wetland_diff < -1 else "stable"
    else:
        trend_water = "stable"
        trend_wetland = "stable"

    return AnalysisSummary(
        partida=partida,
        total_area_ha=round(total_area_ha, 2) if total_area_ha else None,
        date_range=date_range,
        images_analyzed=len(results),
        max_water_ha=round(max_water, 2),
        max_wetland_ha=round(max_wetland, 2),
        avg_water_ha=round(avg_water, 2),
        avg_wetland_ha=round(avg_wetland, 2),
        max_affected_date=max_affected_date,
        max_affected_area_ha=round(max_affected_area, 2),
        trend_water=trend_water,
        trend_wetland=trend_wetland,
    )


async def _save_indices_images_async(
    results: list[ImageResult],
    partida: str,
    output_dir: Path
) -> list[str]:
    """
    Guarda imágenes PNG de índices espectrales de forma asíncrona.

    Retorna lista de paths a las imágenes guardadas.
    """
    saved_paths = []

    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        partida_clean = partida.replace('coords:', 'c').replace(':', '_')

        # Guardar gráfico de evolución
        fechas = [r.date[:10] for r in results]
        agua = [r.water_ha for r in results]
        humedal = [r.wetland_ha for r in results]
        vegetacion = [r.vegetation_ha for r in results]
        otros = [r.other_ha for r in results]

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.bar(fechas, otros, label='Otros', color='#9E9E9E')
        ax.bar(fechas, vegetacion, label='Vegetación', color='#8BC34A', bottom=otros)
        ax.bar(fechas, humedal, label='Humedal', color='#2E7D32',
               bottom=[v + o for v, o in zip(vegetacion, otros)])
        ax.bar(fechas, agua, label='Agua', color='#2196F3',
               bottom=[h + v + o for h, v, o in zip(humedal, vegetacion, otros)])

        ax.set_xlabel('Fecha', fontsize=11, fontweight='bold')
        ax.set_ylabel('Área (hectáreas)', fontsize=11, fontweight='bold')
        ax.set_title(f'Evolución de Clasificación - Partida {partida}', fontsize=13, fontweight='bold')
        ax.legend(loc='upper left', framealpha=0.9)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        img_path = output_dir / f"grafico_{partida_clean}.png"
        plt.savefig(img_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        saved_paths.append(str(img_path))

    except Exception as e:
        logger.warning(f"Error guardando imágenes: {e}")

    return saved_paths


def _save_per_image_visualizations(
    bands,
    indices,
    classification: "np.ndarray",
    parcel_mask: "np.ndarray | None",
    partida_clean: str,
    date_str: str,
    output_dir: Path
) -> ImageUrls:
    """
    Genera y guarda visualizaciones de índices espectrales para una imagen.

    Retorna un objeto ImageUrls con las rutas relativas a /images/.

    Args:
        bands: Bandas descargadas (con b02, b03, b04, etc.)
        indices: Índices espectrales calculados
        classification: Array de clasificación de píxeles
        parcel_mask: Máscara de la parcela (opcional)
        partida_clean: Partida limpiada para nombres de archivo
        date_str: Fecha en formato YYYYMMDD
        output_dir: Directorio de salida

    Returns:
        ImageUrls con las rutas de las imágenes generadas
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import ListedColormap

    output_dir.mkdir(parents=True, exist_ok=True)

    urls = ImageUrls()

    # Configurar colormaps
    cmap_water = plt.cm.RdYlBu_r
    cmap_veg = plt.cm.RdYlGn_r
    cmap_salinity = plt.cm.YlOrRd

    # Colormap para clasificación
    colors_class = ['#9E9E9E', '#2196F3', '#2E7D32', '#8BC34A']
    cmap_class = ListedColormap(colors_class)

    # Índices a guardar (misma estructura que en app.py)
    indices_to_save = [
        ("ndwi", "NDWI", indices.ndwi, cmap_water, -0.5, 0.5),
        ("mndwi", "MNDWI", indices.mndwi, cmap_water, -0.5, 0.5),
        ("ndvi", "NDVI", indices.ndvi, cmap_veg, -0.2, 0.9),
        ("ndmi", "NDMI", indices.ndmi, cmap_veg, -0.2, 0.6),
        ("ndsi", "NDSI", indices.ndsi, cmap_salinity, -0.3, 0.3),
        ("swir2-nir", "SWIR2+NIR", indices.salinity_index, cmap_salinity, 0.3, 0.7),
        ("clasificacion", "Clasificacion", classification, cmap_class, 0, 3),
    ]

    for filename_key, title_name, data, cmap, vmin, vmax in indices_to_save:
        try:
            fig, ax = plt.subplots(figsize=(10, 8))

            if vmin is not None:
                im = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax)
            else:
                im = ax.imshow(data, cmap=cmap)

            plt.colorbar(im, ax=ax, label=title_name)

            # Dibujar perímetro de la parcela sobre todos los índices
            if parcel_mask is not None:
                contour_mask = parcel_mask.astype(float)
                ax.contour(
                    contour_mask,
                    levels=[0.5],
                    colors=['white'],
                    linewidths=2.0,
                    alpha=0.9,
                )

            ax.set_title(f"{title_name} - {partida_clean} | {date_str}",
                        fontsize=10, fontweight='bold')
            ax.axis('off')

            filename = f"{filename_key}_{partida_clean}_{date_str}.png"
            img_path = output_dir / filename
            plt.savefig(img_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)

            # Set URL path (relativa a /images/)
            setattr(urls, filename_key, f"/images/{filename}")

        except Exception as e:
            logger.warning(f"Error guardando {filename_key}: {e}")

    # Generar imagen RGB si tenemos las bandas necesarias
    try:
        if hasattr(bands, 'b04') and hasattr(bands, 'b03') and hasattr(bands, 'b02'):
            # Crear composición RGB
            rgb = np.stack([bands.b04, bands.b03, bands.b02], axis=-1)

            # Realce de contraste (percentile stretch)
            valid_pixels = rgb[rgb > 0]
            if valid_pixels.size > 0:
                p2, p98 = np.percentile(valid_pixels, [2, 98])
                rgb = np.clip((rgb - p2) / (p98 - p2), 0, 1)

            # Aplicar máscara si está disponible (atenuar exterior)
            if parcel_mask is not None:
                mask_3d = np.stack([parcel_mask] * 3, axis=-1)
                rgb_display = np.where(mask_3d, rgb, rgb * 0.3)
            else:
                rgb_display = rgb

            fig, ax = plt.subplots(figsize=(10, 8))
            ax.imshow(rgb_display)

            # Dibujar perímetro de la parcela
            if parcel_mask is not None:
                contour_mask = parcel_mask.astype(float)
                ax.contour(
                    contour_mask,
                    levels=[0.5],
                    colors=['#FF5722'],
                    linewidths=2.0,
                    alpha=0.9,
                )

            ax.set_title(f"Sentinel-2 RGB - Parcela {partida_clean} | {date_str}",
                        fontsize=11, fontweight='bold')
            ax.axis('off')
            plt.tight_layout()

            rgb_filename = f"rgb_{partida_clean}_{date_str}.png"
            rgb_path = output_dir / rgb_filename
            plt.savefig(rgb_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)

            urls.rgb = f"/images/{rgb_filename}"

    except Exception as e:
        logger.warning(f"Error generando imagen RGB: {e}")

    return urls


def load_partidos() -> dict[str, str]:
    """Carga el diccionario de códigos de partidos desde JSON."""
    json_path = Path(__file__).parent.parent / "codigos_partidos_arba.json"
    try:
        import json
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
            return data.get("partidos", {})
    except FileNotFoundError:
        # Fallback a algunos partidos comunes
        return {
            "002": "Alberti",
            "055": "La Plata",
            "014": "Campana",
            "001": "Adolfo Alsina",
        }
