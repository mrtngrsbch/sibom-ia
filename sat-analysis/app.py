"""
Interfaz web Gradio para sat-analysis.

Prueba de concepto para análisis satelital de parcelas catastrales.
"""
import json
import os
from pathlib import Path
import gradio as gr
from datetime import datetime, timedelta

from sat_analysis.services import ArbaService, StacService, PixelClassifier, PartidaParser
from sat_analysis.services.arba import ArbaError
from sat_analysis.services.stac import StacError, get_pixel_area_m2
from sat_analysis.models.schemas import AnalysisResult, ImageResult


def load_partidos() -> dict[str, str]:
    """Carga el diccionario de códigos de partidos desde JSON."""
    json_path = Path(__file__).parent / "codigos_partidos_arba.json"
    try:
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


def analyze_parcel(
    partido: str,  # Dropdown: "002 - Alberti"
    partida: str,  # Textbox: "4606"
    years: int,
    samples_per_year: int,
    max_clouds: int,
    progress: gr.Progress = gr.Progress(),
) -> tuple[str | None, str, str, list[str | None]]:
    """
    Analiza una partida catastral y retorna resultados.

    Args:
        partido: Selección del dropdown (ej: "002 - Alberti")
        partida: Número de partida individual (ej: "4606")
        years: Años de histórico
        samples_per_year: Imágenes por año
        max_clouds: Máximo % de nubes
        progress: Gradio progress tracker

    Returns:
        (grafico_path, tabla_html, resumen_markdown, lista_imagenes_paths)
    """
    if not partida or not partida.strip():
        return None, "", "❌ Ingrese una partida catastral", []

    # Validar rangos
    if not 1 <= years <= 10:
        return None, "", "❌ Años debe estar entre 1 y 10", []

    if not 1 <= samples_per_year <= 12:
        return None, "", "❌ Imágenes por año debe estar entre 1 y 12", []

    if not 0 <= max_clouds <= 100:
        return None, "", "❌ Máximo de nubes debe estar entre 0 y 100", []

    target_images = samples_per_year * years
    execution_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    progress(0, desc="Iniciando análisis...")

    # Extraer código de partido del dropdown
    try:
        codigo_partido = partido.split(" - ")[0].strip()
    except (IndexError, AttributeError):
        return None, "", "❌ Seleccione un partido de la lista", []

    # Parsear partida usando PartidaParser
    try:
        parser = PartidaParser()
        # Combinar codigo_partido + partida individual
        partida_completa = f"{codigo_partido}{partida.zfill(6)}"
        partida_arba = parser.parse(partida_completa)
    except ValueError as e:
        return None, "", f"❌ Error en partida: {e}", []

    progress(
        0.1, desc=f"Consultando parcela {partida_arba.formato_completo}...")

    # 1. Obtener geometría de parcela
    parcel_bbox = None
    total_area_ha = None
    parcel_geometry = None

    try:
        arba = ArbaService()
        # Pasar PartidaARBA parseado
        parcel = arba.get_parcel_geometry(partida_arba)

        if parcel is None:
            return None, "", f"❌ Partida {partida_arba.formato_completo} no encontrada en ARBA", []

        parcel_bbox = parcel.bbox
        parcel_geometry = parcel.geometry
        total_area_ha = parcel.area_approx_hectares

    except ArbaError as e:
        return None, "", f"❌ Error consultando ARBA: {e}", []

    progress(0.2, desc="Buscando imágenes satelitales...")

    # 2. Buscar imágenes
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
            return None, "", "❌ No se encontraron imágenes. Pruebe con más años o menos restricción de nubes", []

    except StacError as e:
        return None, "", f"❌ Error buscando imágenes: {e}", []

    progress(0.3, desc="Procesando imágenes...")

    # 3. Configurar clasificador
    from sat_analysis.config import get_settings
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
    index_images = []
    total_items = len(items)

    # Directorio para imágenes
    script_dir = Path(__file__).parent
    output_dir = script_dir / "web_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Flag para guardar máscara solo una vez
    mask_saved = False

    # Loop de procesamiento de imágenes
    for i, item in enumerate(items):
        progress_val = 0.3 + (0.6 * (i + 1) / total_items)
        progress(progress_val,
                 desc=f"Procesando imagen {i+1}/{total_items}...")

        try:
            bands = stac.download_bands(item, bbox=parcel_bbox, geometry=None)
            pixel_area = get_pixel_area_m2(bands.transform, bands.crs)

            indices = classifier.calculate_indices(
                b02=bands.b02, b03=bands.b03, b04=bands.b04,
                b08=bands.b08, b11=bands.b11, b12=bands.b12,
            )

            result = classifier.classify_with_areas(
                indices, pixel_area_m2=pixel_area)

            # Crear y aplicar máscara específica para esta imagen
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
                # Guardar imagen de máscara SOLO la primera vez
                if not mask_saved:
                    mask_path = _save_mask_image(
                        parcel_mask, partida, output_dir)
                    if mask_path:
                        index_images.append(mask_path)
                    mask_saved = True

            water_ha = result.areas_hectares.get(1, 0)
            wetland_ha = result.areas_hectares.get(2, 0)
            vegetation_ha = result.areas_hectares.get(3, 0)
            other_ha = result.areas_hectares.get(0, 0)

            results.append(ImageResult(
                date=item.datetime,
                water_ha=round(water_ha, 2),
                wetland_ha=round(wetland_ha, 2),
                vegetation_ha=round(vegetation_ha, 2),
                other_ha=round(other_ha, 2),
                cloud_cover=item.cloud_cover,
            ))

            # Guardar imágenes de índices (SIN máscara - ya se creó una vez)
            image_date_str = item.datetime[:10]
            saved_paths = _save_indices_images(
                indices=indices,
                classification=result.classification,
                partida=partida,
                image_date=image_date_str,
                output_dir=output_dir,
            )
            index_images.extend(saved_paths)

        except StacError:
            continue

    if not results:
        return None, "", "❌ Error procesando todas las imágenes", []

    progress(0.95, desc="Generando reporte...")

    # 4. Generar gráfico de evolución
    grafico_path = _generate_classification_chart(results, partida, output_dir)

    # 5. Generar tabla HTML
    table_html = _generate_results_table(results, total_area_ha)

    # 6. Generar informe completo
    resumen = _generate_full_report(
        results=results,
        total_area_ha=total_area_ha,
        target_images=target_images,
        partida=partida,
        date_range=date_range,
        execution_time=execution_time,
        parcel_bbox=parcel_bbox,
    )

    progress(1.0, desc="¡Análisis completo!")

    return grafico_path, table_html, resumen, index_images


def _save_mask_image(parcel_mask, partida: str, output_dir: Path) -> str | None:
    """Guarda la imagen de máscara de la parcela (UNA SOLA VEZ)."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 8))
        ax.imshow(parcel_mask, cmap=plt.cm.gray_r, interpolation='none')
        plt.colorbar(ax.images[0], ax=ax, label="Máscara Parcela")
        ax.set_title(f"Máscara Parcela - {partida}",
                     fontsize=12, fontweight='bold')
        ax.axis('off')

        partida_clean = partida.replace('coords:', 'c').replace(':', '_')
        img_path = output_dir / f"mascara_{partida_clean}.png"
        plt.savefig(img_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        return str(img_path)
    except Exception:
        return None


def _save_indices_images(
    indices,
    classification,
    partida: str,
    image_date: str,
    output_dir: Path,
) -> list[str]:
    """
    Guarda imágenes PNG de índices espectrales (SIN máscara - se crea por separado).
    Retorna lista de paths a las imágenes guardadas.
    """
    saved_paths = []

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        return saved_paths

    image_date_formatted = image_date.replace("-", "")
    partida_clean = partida.replace('coords:', 'c').replace(':', '_')

    # Configurar colormaps
    cmap_water = plt.cm.RdYlBu_r
    cmap_veg = plt.cm.RdYlGn_r
    cmap_salinity = plt.cm.YlOrRd

    # Colormap para clasificación
    from matplotlib.colors import ListedColormap
    colors_class = ['#9E9E9E', '#2196F3', '#2E7D32', '#8BC34A']
    cmap_class = ListedColormap(colors_class)

    # Índices a guardar (7 imágenes por fecha)
    indices_to_save = [
        ("ndwi", "NDWI", indices.ndwi, cmap_water, -0.5, 0.5),
        ("mndwi", "MNDWI", indices.mndwi, cmap_water, -0.5, 0.5),
        ("ndvi", "NDVI", indices.ndvi, cmap_veg, -0.2, 0.9),
        ("ndmi", "NDMI", indices.ndmi, cmap_veg, -0.2, 0.6),
        ("ndsi", "NDSI", indices.ndsi, cmap_salinity, -0.3, 0.3),
        ("swir2-nir", "SWIR2 + NIR (Salinity)",
         indices.salinity_index, cmap_salinity, 0.3, 0.7),
        ("clasificacion", "Clasificacion", classification, cmap_class, 0, 3),
    ]

    for filename_name, title_name, data, cmap, vmin, vmax in indices_to_save:
        try:
            fig, ax = plt.subplots(figsize=(10, 8))

            if vmin is not None:
                im = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax)
            else:
                im = ax.imshow(data, cmap=cmap)

            plt.colorbar(im, ax=ax, label=title_name)
            ax.set_title(f"{title_name} - {partida} | {image_date}",
                         fontsize=10, fontweight='bold')
            ax.axis('off')

            filename = f"{filename_name}_{partida_clean}_{image_date_formatted}.png"
            img_path = output_dir / filename
            plt.savefig(img_path, dpi=150,
                        bbox_inches='tight', facecolor='white')
            plt.close(fig)

            saved_paths.append(str(img_path))

        except Exception:
            continue

    return saved_paths


def _generate_classification_chart(results: list[ImageResult], partida: str, output_dir: Path) -> str | None:
    """Genera un gráfico de barras apiladas con la evolución temporal."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fechas = [r.date[:10] for r in results]
        agua = [r.water_ha for r in results]
        humedal = [r.wetland_ha for r in results]
        vegetacion = [r.vegetation_ha for r in results]
        otros = [r.other_ha for r in results]

        fig, ax = plt.subplots(figsize=(12, 5))

        ax.bar(fechas, otros, label='Otros', color='#9E9E9E')
        ax.bar(fechas, vegetacion, label='Vegetación',
               color='#8BC34A', bottom=otros)
        ax.bar(fechas, humedal, label='Humedal', color='#2E7D32',
               bottom=[v + o for v, o in zip(vegetacion, otros)])
        ax.bar(fechas, agua, label='Agua', color='#2196F3',
               bottom=[h + v + o for h, v, o in zip(humedal, vegetacion, otros)])

        ax.set_xlabel('Fecha', fontsize=11, fontweight='bold')
        ax.set_ylabel('Área (hectáreas)', fontsize=11, fontweight='bold')
        ax.set_title(
            f'Evolución de Clasificación - Partida {partida}', fontsize=13, fontweight='bold')
        ax.legend(loc='upper left', framealpha=0.9)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        img_path = output_dir / \
            f"grafico_{partida.replace('coords:', 'c').replace(':', '_')}.png"
        plt.savefig(img_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        return str(img_path)

    except Exception:
        return None


def _generate_results_table(results: list[ImageResult], total_area_ha: float | None) -> str:
    """Genera tabla HTML con resultados."""
    rows = []
    for r in results:
        fecha = r.date[:10] if len(r.date) > 10 else r.date
        nubes = f"{r.cloud_cover:.0f}%" if r.cloud_cover is not None else "N/A"
        total = r.water_ha + r.wetland_ha + r.vegetation_ha + r.other_ha
        afectado_pct = ((r.water_ha + r.wetland_ha) /
                        total * 100) if total > 0 else 0

        rows.append(f"""
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 12px 8px; color: #333;">{fecha}</td>
                <td style="text-align: right; padding: 12px 8px; color: #2196F3; font-weight: 500;">{r.water_ha:.1f}</td>
                <td style="text-align: right; padding: 12px 8px; color: #2E7D32; font-weight: 500;">{r.wetland_ha:.1f}</td>
                <td style="text-align: right; padding: 12px 8px; color: #8BC34A; font-weight: 500;">{r.vegetation_ha:.1f}</td>
                <td style="text-align: right; padding: 12px 8px; color: #757575;">{r.other_ha:.1f}</td>
                <td style="text-align: right; padding: 12px 8px; color: #757575;">{nubes}</td>
                <td style="text-align: right; padding: 12px 8px; color: #333; font-weight: bold;">{afectado_pct:.1f}%</td>
            </tr>
        """)

    area_info = f"<p style='margin: 0 0 15px 0; font-size: 14px;'><strong>Área total:</strong> {total_area_ha:.1f} ha</p>" if total_area_ha else ""

    return f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            {area_info}
            <table style="border-collapse: collapse; width: 100%; margin-top: 10px; font-size: 14px;">
                <thead>
                    <tr style="background: #e3f2fd;">
                        <th style="padding: 12px 8px; text-align: left; color: #000; font-weight: bold; border-bottom: 2px solid #1976D2;">Fecha</th>
                        <th style="padding: 12px 8px; text-align: right; color: #000; font-weight: bold; border-bottom: 2px solid #1976D2;">Agua (ha)</th>
                        <th style="padding: 12px 8px; text-align: right; color: #000; font-weight: bold; border-bottom: 2px solid #1976D2;">Humedal (ha)</th>
                        <th style="padding: 12px 8px; text-align: right; color: #000; font-weight: bold; border-bottom: 2px solid #1976D2;">Vegetación (ha)</th>
                        <th style="padding: 12px 8px; text-align: right; color: #000; font-weight: bold; border-bottom: 2px solid #1976D2;">Otros (ha)</th>
                        <th style="padding: 12px 8px; text-align: right; color: #000; font-weight: bold; border-bottom: 2px solid #1976D2;">Nubes</th>
                        <th style="padding: 12px 8px; text-align: right; color: #000; font-weight: bold; border-bottom: 2px solid #1976D2;">Afectado</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
    """


def _generate_full_report(
    results: list[ImageResult],
    total_area_ha: float | None,
    target_images: int,
    partida: str,
    date_range: str,
    execution_time: str,
    parcel_bbox: list[float],
) -> str:
    """Genera informe completo en Markdown."""
    if not results:
        return "No hay resultados para el informe"

    max_water = max(r.water_ha for r in results)
    max_wetland = max(r.wetland_ha for r in results)
    min_water = min(r.water_ha for r in results)
    min_wetland = min(r.wetland_ha for r in results)
    avg_water = sum(r.water_ha for r in results) / len(results)
    avg_wetland = sum(r.wetland_ha for r in results) / len(results)

    max_affected_result = max(results, key=lambda r: r.water_ha + r.wetland_ha)
    max_affected_date = max_affected_result.date[:10]
    max_affected_area = max_affected_result.water_ha + max_affected_result.wetland_ha

    first = results[0]
    last = results[-1]
    water_diff = last.water_ha - first.water_ha
    wetland_diff = last.wetland_ha - first.wetland_ha

    trend_water = "↗️ **SUBIENDO**" if water_diff > 1 else "↘️ **BAJANDO**" if water_diff < - \
        1 else "➡️ **ESTABLE**"
    trend_wetland = "↗️ **SUBIENDO**" if wetland_diff > 1 else "↘️ **BAJANDO**" if wetland_diff < - \
        1 else "➡️ **ESTABLE**"

    affected_pct = ""
    if total_area_ha and total_area_ha > 0:
        max_affected_pct = (max_affected_area / total_area_ha) * 100
        affected_pct = f"\n**Porcentaje máximo afectado:** {max_affected_area:.1f} ha (**{max_affected_pct:.1f}%** del total)"

    trend_lines = []
    if len(results) >= 2:
        trend_lines = [
            "",
            "### 📈 Tendencias",
            "",
            f"| Categoría | Primera | Última | Cambio | Tendencia |",
            f"|-----------|--------|--------|--------|-----------|",
            f"| Agua | {first.water_ha:.1f} ha | {last.water_ha:.1f} ha | {water_diff:+.1f} ha | {trend_water} |",
            f"| Humedal | {first.wetland_ha:.1f} ha | {last.wetland_ha:.1f} ha | {wetland_diff:+.1f} ha | {trend_wetland} |",
        ]

    from sat_analysis.config import get_settings
    settings = get_settings()

    lines = [
        "# 📊 Informe Completo de Análisis",
        "",
        f"**Partida:** {partida}",
        f"**Fecha de ejecución:** {execution_time}",
        f"**Período analizado:** {date_range}",
        f"**Imágenes procesadas:** {len(results)} de {target_images} objetivo",
        f"**Coordenadas (BBOX):** `{parcel_bbox}`",
        "",
        "---",
        "",
        "## 🎯 Resumen Ejecutivo",
        "",
        f"**Área total:** {total_area_ha:.1f} ha" if total_area_ha else "",
        "",
        f"| Métrica | Valor |",
        f"|---------|-------|",
        f"| Agua máxima | {max_water:.1f} ha ({min_water:.1f} - {max_water:.1f} ha) |",
        f"| Humedal máximo | {max_wetland:.1f} ha ({min_wetland:.1f} - {max_wetland:.1f} ha) |",
        f"| Agua promedio | {avg_water:.1f} ha |",
        f"| Humedal promedio | {avg_wetland:.1f} ha |",
        f"| **Pico de anegamiento** | {max_affected_area:.1f} ha el {max_affected_date} |",
        affected_pct,
    ]

    lines.extend(trend_lines)

    lines.extend([
        "",
        "---",
        "",
        "## 🔬 Umbrales de Clasificación Utilizados",
        "",
        f"| Índice | Umbral | Valor |",
        f"|--------|--------|-------|",
        f"| Agua (NDWI) | > {settings.water_ndwi_threshold} | Agua detectada |",
        f"| Agua turbia (MNDWI) | > {settings.water_mndwi_threshold} | Agua turbia |",
        f"| Humedal (NDVI) | > {settings.wetland_ndvi_threshold} | Vegetación húmeda |",
        f"| Humedal (NDMI) | > {settings.wetland_ndmi_threshold} | Contenido de humedad |",
        f"| Vegetación (NDVI) | > {settings.vegetation_ndvi_threshold} | Vegetación seca |",
        "",
        "*Umbrales validados según literatura científica peer-reviewed.*",
        "",
        "---",
        "",
        "## 📋 Detalle de Imágenes Analizadas",
        "",
        "| Fecha | Agua (ha) | Humedal (ha) | Veg (ha) | Otros (ha) | Nubes | Afectado % |",
        "|-------|-----------|--------------|----------|------------|-------|------------|",
    ])

    for r in results:
        fecha = r.date[:10] if len(r.date) > 10 else r.date
        nubes = f"{r.cloud_cover:.0f}%" if r.cloud_cover is not None else "N/A"
        total = r.water_ha + r.wetland_ha + r.vegetation_ha + r.other_ha
        afectado_pct = ((r.water_ha + r.wetland_ha) /
                        total * 100) if total > 0 else 0
        lines.append(
            f"| {fecha} | {r.water_ha:.1f} | {r.wetland_ha:.1f} | {r.vegetation_ha:.1f} | {r.other_ha:.1f} | {nubes} | {afectado_pct:.1f}% |")

    lines.extend([
        "",
        "---",
        "",
        "## ℹ️ Información Técnica",
        "",
        "- **Fuente de datos:** Sentinel-2 L2A (MSI)",
        "- **Proveedor:** Microsoft Planetary Computer (STAC)",
        "- **Resolución espacial:** 10 metros por píxel",
        "- **Índices calculados:** NDWI, MNDWI, NDVI, NDMI, NDSI, Salinity Index",
        "- **Clasificación:** 4 categorías (Agua, Humedal, Vegetación, Otros)",
        "",
        "---",
        "",
    ])

    return "\n".join(lines)


# Crear interfaz Gradio
def create_ui() -> gr.Blocks:
    """Crea y retorna la interfaz de usuario Gradio."""

    # Cargar partidos para el dropdown
    partidos_dict = load_partidos()
    partido_choices = [
        f"{codigo} - {nombre}"
        for codigo, nombre in sorted(partidos_dict.items(), key=lambda x: x[1])
    ]

    with gr.Blocks(
        title="Sat-Analysis - Análisis Satelital",
    ) as app:
        gr.Markdown(
            """
            # 🛰️ Sat-Analysis - Análisis Satelital de Parcelas de PBA

            Sistema de detección de anegamiento y salinización para la provincia de Buenos Aires, usando imágenes de la misión [**Sentinel-2**](https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-data/sentinel-2).
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 🔍 Parámetros de Búsqueda")

                # Selector de partido (dropdown)
                partido_dropdown = gr.Dropdown(
                    choices=partido_choices,
                    value="002 - Alberti",
                    label="Partido / Municipio",
                    info="Seleccione el partido de la partida",
                    interactive=True,
                    filterable=True,
                )

                # Input de partida individual
                partida_input = gr.Textbox(
                    label="Número de Partida",
                    placeholder="Ej: 4606",
                    info="Partida individual (se completará con ceros a la izquierda)",
                    value="4606",
                )

                gr.Markdown(
                    """
                    <small style="color: #666;">
                    Formato final: <strong>002-004606</strong> (Partido + Partida)
                    </small>
                    """,
                )

                with gr.Row():
                    years_input = gr.Slider(
                        minimum=1,
                        maximum=10,
                        value=2,
                        step=1,
                        label="Años de histórico",
                        info="Período a analizar",
                    )
                    samples_input = gr.Slider(
                        minimum=1,
                        maximum=12,
                        value=4,
                        step=1,
                        label="Imágenes por año",
                        info="4 = trimestral",
                    )

                clouds_input = gr.Slider(
                    minimum=0,
                    maximum=100,
                    value=20,
                    step=5,
                    label="Máximo % de nubes",
                    info="Menor = más restrictivo",
                )

                analyze_btn = gr.Button(
                    "🚀 Analizar Parcela",
                    variant="primary",
                    size="lg",
                )

            with gr.Column(scale=2):
                gr.Markdown("### 📈 Resultados")

                with gr.Tabs():
                    with gr.Tab("📊 Gráfico"):
                        grafico_output = gr.Image(
                            label="Evolución Temporal",
                            show_label=True,
                            height=350,
                        )

                    with gr.Tab("📋 Tabla"):
                        table_output = gr.HTML(
                            value="<p style='color: #666; text-align: center; padding: 40px;'>Ingrese una partida y haga clic en Analizar</p>",
                        )

                    with gr.Tab("📄 Informe"):
                        report_output = gr.Markdown(
                            value="*El informe completo aparecerá aquí*",
                        )

                    with gr.Tab("🖼️ Imágenes"):
                        images_output = gr.Gallery(
                            label="Imágenes de Clasificación",
                            show_label=True,
                            columns=3,
                            rows=2,
                            height=500,
                            object_fit="contain",
                        )

        # Event handlers
        analyze_btn.click(
            fn=analyze_parcel,
            inputs=[partido_dropdown, partida_input,
                    years_input, samples_input, clouds_input],
            outputs=[grafico_output, table_output,
                     report_output, images_output],
        )

        gr.Markdown(
            """
            ---

            ### ℹ️ Información

            | Aspecto | Detalle |
            |---------|---------|
            | **Datos** | Sentinel-2 L2A |
            | **Proveedor** | Microsoft Planetary Computer |
            | **Resolución** | 10m por píxel |
            | **Índices** | NDWI, MNDWI, NDVI, NDMI, NDSI, Salinity |
            | **Validación** | Umbrales peer-reviewed ✅ |

            """
        )

    return app


# Crear la app para Railway
app = create_ui()

# Para Railway: exponer la app como variable module-level
if __name__ == "__main__":
    # Railway asigna puerto vía variable de entorno PORT
    # Si no existe, usar 7860 como default (local development)
    port = int(os.getenv("PORT", "7860"))
    server_name = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")

    app.launch(
        server_name=server_name,
        server_port=port,
        theme=gr.themes.Soft(),
        css="""
            .gradio-container { max-width: 1400px !important; }
            h1 { font-size: 2.2rem !important; }
            h2 { font-size: 1.5rem !important; }
            table { font-size: 0.9rem !important; }
            th { font-weight: bold !important; }
        """
    )
