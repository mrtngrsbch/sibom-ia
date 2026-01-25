"""
Interfaz de línea de comandos para sat-analysis.

Usa Typer para CLI y Rich para output formateado en terminal.
"""
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from datetime import datetime, timedelta
import json
from pathlib import Path
import logging
from io import StringIO
import os

from .services import ArbaService, StacService, PixelClassifier
from .services.stac import get_pixel_area_m2
from .models.schemas import AnalysisResult, ImageResult
from .config import get_settings
from .services.arba import ArbaError
from .services.stac import StacError


class LogCapture:
    """Captura output de terminal para guardar en archivo de log."""

    # Tags de Rich a limpiar
    RICH_TAGS = [
        "[cyan]", "[/cyan]", "[green]", "[/green]", "[red]", "[/red]",
        "[yellow]", "[/yellow]", "[blue]", "[/blue]", "[dim]", "[/dim]",
        "[bold]", "[/bold]", "[bright_green]", "[/bright_green]",
        "[bold green]", "[/bold green]", "[/bold]", "[/bright_green]",
    ]

    def __init__(self):
        self.buffer = StringIO()
        self.original_print = None

    def _clean_text(self, text: str) -> str:
        """Elimina tags de Rich y convierte a texto plano."""
        # Eliminar tags de Rich
        for tag in self.RICH_TAGS:
            text = text.replace(tag, "")
        # Eliminar referencias a objetos Rich (incluido NewLine)
        import re
        text = re.sub(r'<rich\.\w+\.Table object at 0x[0-9a-fA-F]+>', '', text)
        text = re.sub(r'<rich\.console\.NewItem object at 0x[0-9a-fA-F]+>', '', text)
        text = re.sub(r'<rich\.console\.Renderable object at 0x[0-9a-fA-F]+>', '', text)
        text = re.sub(r'<\w+ object at 0x[0-9a-fA-F]+>', '', text)
        # Limpiar espacios múltiples
        text = re.sub(r'  +', ' ', text)  # múltiples espacios a uno
        return text.strip()

    def start(self):
        """Inicia captura de console.print."""
        self.original_print = console.print
        console.print = self._capture_print

    def _capture_print(self, *args, **kwargs):
        """Captura y llama al print original."""
        # Ignorar objetos NewLine y otros objetos de renderizado de Rich
        # que solo sirven para formatear la terminal
        for arg in args:
            arg_str = str(arg)
            # Si es un objeto interno de Rich (NewLine, etc.), ignorar
            if arg_str.startswith('<rich.console.') or arg_str.startswith('<rich.live.'):
                self.original_print(*args, **kwargs)
                return

        # Capturar en buffer (sin tags de formato)
        message = " ".join(str(arg) for arg in args)
        clean_message = self._clean_text(message)

        # Solo escribir si hay contenido real (no vacío después de limpiar)
        if clean_message:
            self.buffer.write(clean_message + "\n")

        # También mostrar en terminal (con formato)
        self.original_print(*args, **kwargs)

    def stop(self):
        """Detiene captura."""
        if self.original_print:
            console.print = self.original_print

    def get_content(self) -> str:
        """Retorna contenido capturado y limpiado."""
        return self._clean_final_content(self.buffer.getvalue())

    def _clean_final_content(self, content: str) -> str:
        """Limpia el contenido final del log antes de guardarlo."""
        import re

        # Eliminar líneas que contengan solo referencias a objetos Rich
        lines = content.split('\n')
        cleaned_lines = []

        for line in lines:
            # Ignorar líneas con objetos Rich
            if '<rich.console.' in line or '<rich.live.' in line:
                continue
            # Ignorar líneas que son solo referencias a objetos
            if re.match(r'^<\w+ object at 0x[0-9a-fA-F]+>$', line.strip()):
                continue
            cleaned_lines.append(line)

        # Unir líneas y limitar líneas vacías consecutivas a máximo 2
        result = '\n'.join(cleaned_lines)
        # Reemplazar 3 o más nuevas consecutivas por exactamente 2
        result = re.sub(r'\n\n\n+', '\n\n', result)

        return result

    def save(self, filepath: str | Path):
        """Guarda log en archivo con contenido limpio."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        cleaned_content = self._clean_final_content(self.buffer.getvalue())
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(cleaned_content)

    def write_table(self, title: str, headers: list[str], rows: list[list[str]]):
        """Escribe una tabla en formato texto plano al log."""
        self.buffer.write(f"\n{title}\n")
        self.buffer.write("=" * len(title) + "\n")

        # Calcular ancho de columnas
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))

        # Header
        header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        self.buffer.write(header_line + "\n")
        self.buffer.write("-" * len(header_line) + "\n")

        # Rows
        for row in rows:
            row_line = " | ".join(str(cell).ljust(col_widths[i]) if i < len(col_widths) else str(cell)
                                   for i, cell in enumerate(row))
            self.buffer.write(row_line + "\n")
        self.buffer.write("\n")

app = typer.Typer(
    name="sat-analysis",
    help="Sistema de detección de anegamiento usando imágenes satelitales",
    add_completion=False,
)
console = Console()


def _save_indices_images(
    indices,
    classification,
    partida: str,
    image_date: str,
    output_dir: str,
    parcel_mask=None,
):
    """Guarda imágenes PNG de los índices espectrales."""
    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        console.print("[yellow]WARNING: matplotlib no instalado, no se guardarán imágenes[/yellow]")
        return

    # Convertir a ruta absoluta si es relativa
    output_path = Path(output_dir)
    if not output_path.is_absolute():
        # Obtener ruta base del script (sat-analysis/)
        script_dir = Path(__file__).parent.parent.parent
        output_path = script_dir / output_dir

    os.makedirs(output_path, exist_ok=True)

    # Formatear fecha para nombre de archivo
    image_date_formatted = image_date.replace("-", "")  # YYYYMMDD

    # Configurar colormaps
    cmap_water = plt.cm.RdYlBu_r  # Azul para valores bajos (agua)
    cmap_veg = plt.cm.RdYlGn_r  # Verde para valores altos (vegetación)

    # Índices a guardar
    indices_to_save = [
        ("NDWI", indices.ndwi, cmap_water, -0.5, 0.5),
        ("MNDWI", indices.mndwi, cmap_water, -0.5, 0.5),
        ("NDVI", indices.ndvi, cmap_veg, -0.2, 0.9),
        ("NDMI", indices.ndmi, cmap_veg, -0.2, 0.6),
        ("Clasificacion", classification, plt.cm.tab10, None, None),
    ]

    # Agregar máscara si está disponible
    if parcel_mask is not None:
        indices_to_save.append(("Mascara", parcel_mask.astype(np.uint8), plt.cm.gray_r, 0, 1))

    for name, data, cmap, vmin, vmax in indices_to_save:
        fig, ax = plt.subplots(figsize=(10, 8))

        if vmin is not None:
            im = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax)
        else:
            im = ax.imshow(data, cmap=cmap)

        plt.colorbar(im, ax=ax, label=name)
        ax.set_title(f"{name} - {partida} | STAC Planetary Computer | {image_date}", fontsize=10)
        ax.axis('off')

        filename = f"{output_path}/{name.lower()}_{partida}_{image_date_formatted}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close(fig)


@app.command()
def analyze(
    partida: str = typer.Argument(..., help="Partida catastral ARBA (ej: 4606) o 'coords:lon,lat,lon,lat'"),
    years: int = typer.Option(2, "--years", "-y", help="Años de histórico a analizar (1-10)"),
    max_images: int = typer.Option(10, "--max-images", "-n", help="Máximo de imágenes a procesar"),
    max_clouds: int = typer.Option(20, "--max-clouds", "-c", help="Máximo % de nubes (0-100)"),
    output: str = typer.Option(None, "--output", "-o", help="Archivo JSON de salida"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Output detallado"),
    logs_dir: str = typer.Option("logs", "--logs-dir", "-l", help="Directorio para archivos de log"),
    images_dir: str = typer.Option("logs_images", "--images-dir", "-i", help="Directorio para imágenes (dentro de sat-analysis)"),
):
    """
    Analiza una partida catastral para detectar anegamiento.

    Busca imágenes satelitales Sentinel-2, calcula índices espectrales
    y clasifica píxeles en agua, humedal y vegetación.

    Las imágenes de índices se guardan automáticamente en cada ejecución.

    Para usar coordenadas fijas en lugar de partida:
    sat-analysis analyze coords:-59.5,-35.2,-59.4,-35.1
    """
    # Iniciar captura de log
    log_capture = LogCapture()
    log_capture.start()

    # Variables para el log (definidas antes del try para usar en finally)
    execution_datetime = datetime.now()
    execution_date = execution_datetime.strftime("%Y-%m-%d")
    execution_time = execution_datetime.strftime("%H%M%S")
    parcel_id = partida
    log_path = None

    try:
        # Header del log
        console.print(f"# Análisis sat-analysis - {execution_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        console.print(f"# Partida: {partida}")
        console.print(f"# Período: {years} años")
        console.print(f"#" + "="*60)
        # Validar rangos
        if not 1 <= years <= 10:
            console.print("[red]ERROR: --years debe estar entre 1 y 10[/red]")
            raise typer.Exit(1)

        if not 0 <= max_clouds <= 100:
            console.print("[red]ERROR: --max-clouds debe estar entre 0 y 100[/red]")
            raise typer.Exit(1)

        # Parsear coordenadas si se usa modo coords
        bbox = None
        area_approx = None

        if partida.startswith("coords:"):
            # Formato: coords:min_lon,min_lat,max_lon,max_lat
            try:
                coords_str = partida.replace("coords:", "").strip()
                bbox = [float(x) for x in coords_str.split(",")]
                if len(bbox) != 4:
                    raise ValueError("Se requieren 4 valores")
                console.print(f"[cyan]> Usando coordenadas: {bbox}[/cyan]")
            except Exception as e:
                console.print(f"[red]ERROR: Error parseando coordenadas: {e}[/red]")
                console.print("[dim]   Formato: coords:min_lon,min_lat,max_lon,max_lat[/dim]")
                raise typer.Exit(1)
        else:
            console.print(f"[cyan]> Consultando partida {partida}...[/cyan]")

        # 1. Obtener geometría de parcela desde ARBA (o usar coords fijas)
        parcel_bbox = None
        total_area_ha = None

        if bbox is not None:
            # Modo coords: usar bbox directamente
            parcel_bbox = bbox
            console.print(f"[green]OK Usando área definida[/green]")
            # Calcular área aproximada del bbox
            lon_diff = (bbox[2] - bbox[0]) * 91  # km
            lat_diff = (bbox[3] - bbox[1]) * 111  # km
            total_area_ha = lon_diff * lat_diff * 100  # km² a ha
        else:
            # Modo partida: consultar ARBA
            parcel_geometry = None
            try:
                arba = ArbaService()
                parcel = arba.get_parcel_geometry(partida)

                if parcel is None:
                    console.print(f"[red]ERROR: Partida {partida} no encontrada[/red]")
                    console.print("[dim]   Verifica que el número sea correcto[/dim]")
                    console.print("[dim]   También puedes usar coords:min_lon,min_lat,max_lon,max_lat[/dim]")
                    raise typer.Exit(1)

                parcel_bbox = parcel.bbox
                parcel_geometry = parcel.geometry
                total_area_ha = parcel.area_approx_hectares
                console.print(f"[green]OK Parcela encontrada[/green]")
                console.print(f"   BBOX: {parcel.bbox}")
                if total_area_ha:
                    console.print(f"   Área: {total_area_ha:.1f} ha (desde ARBA)")

            except ArbaError as e:
                console.print(f"[red]ERROR: Error consultando ARBA: {e}[/red]")
                console.print("[yellow]TIP: Tip: Puedes usar coordenadas fijas en lugar de partida:[/yellow]")
                console.print("[dim]   sat-analysis analyze coords:-59.5,-35.2,-59.4,-35.1[/dim]")
                raise typer.Exit(1)

        # 2. Buscar imágenes Sentinel-2
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        date_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"

        console.print(f"\n[cyan]SATELITE: Buscando imágenes...[/cyan]")
        console.print(f"   Período: {date_range}")
        console.print(f"   Máx nubes: {max_clouds}%")

        try:
            stac = StacService()
            items = stac.search_sentinel(
                bbox=parcel_bbox,
                date_range=date_range,
                max_clouds=float(max_clouds),
                limit=max_images,
            )

            if not items:
                console.print("[yellow]WARNING: No se encontraron imágenes[/yellow]")
                console.print("[dim]   Intenta con un rango de fechas mayor o menos restricción de nubes[/dim]")
                raise typer.Exit(1)

            console.print(f"[green]OK {len(items)} imágenes encontradas[/green]")

        except StacError as e:
            console.print(f"[red]ERROR: Error buscando imágenes: {e}[/red]")
            raise typer.Exit(1)

        # 3. Procesar imágenes
        console.print(f"\n[cyan]PROCESANDO: Procesando imágenes...[/cyan]")
        results = []
        classifier = PixelClassifier()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:

            task = progress.add_task(
                "Descargando y clasificando...", total=len(items)
            )

            for item in items:
                if verbose:
                    console.print(f"\n[dim]   Procesando: {item.datetime[:10]} ({item.cloud_cover:.1f}% nubes)[/dim]")

                try:
                    # Descargar bandas (solo bbox por ahora, el clip por geometría es experimental)
                    bands = stac.download_bands(
                        item, bbox=parcel_bbox, geometry=None
                    )

                    # Calcular área del píxel desde el transform affine
                    pixel_area = get_pixel_area_m2(bands.transform, bands.crs)

                    if verbose:
                        console.print(f"[dim]   Área píxel: {pixel_area:.1f} m²[/dim]")

                    # Crear máscara de la parcela (solo si tenemos geometría)
                    parcel_mask = None
                    if bbox is None and 'parcel_geometry' in locals() and parcel_geometry is not None:
                        parcel_mask = stac.create_parcel_mask(
                            shape=bands.b02.shape,
                            geometry=parcel_geometry,
                            bbox=parcel_bbox,
                            image_crs=bands.crs,
                            transform=bands.transform
                        )

                        if verbose:
                            pixels_inside = parcel_mask.sum()
                            total_pixels = parcel_mask.size
                            coverage = pixels_inside / total_pixels * 100
                            console.print(f"[dim]   Píxeles parcela: {pixels_inside:,}/{total_pixels:,} ({coverage:.1f}%)[/dim]")

                    # Calcular índices
                    indices = classifier.calculate_indices(
                        b02=bands.b02,
                        b03=bands.b03,
                        b04=bands.b04,
                        b08=bands.b08,
                        b11=bands.b11,
                    )

                    # Clasificar y calcular áreas
                    result = classifier.classify_with_areas(indices, pixel_area_m2=pixel_area)

                    # Aplicar máscara de parcela si está disponible
                    if parcel_mask is not None:
                        result = classifier.apply_mask(
                            classification=result.classification,
                            areas_hectares=result.areas_hectares,
                            mask=parcel_mask,
                            pixel_area_m2=pixel_area
                        )

                    # Extraer áreas (ya corregidas por la máscara si se aplicó)
                    water_ha = result.areas_hectares.get(1, 0)
                    wetland_ha = result.areas_hectares.get(2, 0)
                    vegetation_ha = result.areas_hectares.get(3, 0)
                    other_ha = result.areas_hectares.get(0, 0)

                    # Guardar imágenes de índices (siempre)
                    image_date_str = item.datetime[:10]  # YYYY-MM-DD
                    _save_indices_images(
                        indices=indices,
                        classification=result.classification,
                        partida=partida,
                        image_date=image_date_str,
                        output_dir=images_dir,
                        parcel_mask=parcel_mask,
                    )

                    results.append(
                        ImageResult(
                            date=item.datetime,
                            water_ha=round(water_ha, 2),
                            wetland_ha=round(wetland_ha, 2),
                            vegetation_ha=round(vegetation_ha, 2),
                            other_ha=round(other_ha, 2),
                            cloud_cover=item.cloud_cover,
                        )
                    )

                except StacError as e:
                    console.print(f"[yellow]WARNING: Error procesando imagen {item.datetime}: {e}[/yellow]")
                    continue

                progress.advance(task)

        # 4. Mostrar resultados
        console.print(f"\n[bold green]RESULTADOS: Resultados del Análisis[/bold green]")

        table = Table(title=f"Evolución temporal - Partida {partida}")
        table.add_column("Fecha", style="cyan", no_wrap=True)
        table.add_column("Agua (ha)", justify="right", style="blue")
        table.add_column("Humedal (ha)", justify="right", style="green")
        table.add_column("Vegetación (ha)", justify="right", style="bright_green")
        table.add_column("Otros (ha)", justify="right", style="dim")
        table.add_column("Nubes %", justify="right", style="dim")

        for r in results:
            # Formatear fecha
            fecha = r.date[:10] if len(r.date) > 10 else r.date
            nubes = f"{r.cloud_cover:.0f}" if r.cloud_cover is not None else "N/A"

            table.add_row(
                fecha,
                f"{r.water_ha:.1f}",
                f"{r.wetland_ha:.1f}",
                f"{r.vegetation_ha:.1f}",
                f"{r.other_ha:.1f}",
                nubes,
            )

        console.print(table)

        # Escribir tabla en log en formato texto plano
        table_headers = ["Fecha", "Agua (ha)", "Humedal (ha)", "Vegetación (ha)", "Otros (ha)", "Nubes %"]
        table_rows = []
        for r in results:
            fecha = r.date[:10] if len(r.date) > 10 else r.date
            nubes = f"{r.cloud_cover:.0f}" if r.cloud_cover is not None else "N/A"
            table_rows.append([
                fecha,
                f"{r.water_ha:.1f}",
                f"{r.wetland_ha:.1f}",
                f"{r.vegetation_ha:.1f}",
                f"{r.other_ha:.1f}",
                nubes,
            ])
        log_capture.write_table(f"Evolución temporal - Partida {partida}", table_headers, table_rows)

        # 5. Resumen
        if results:
            max_water = max(r.water_ha for r in results)
            max_wetland = max(r.wetland_ha for r in results)
            avg_water = sum(r.water_ha for r in results) / len(results)
            avg_wetland = sum(r.wetland_ha for r in results) / len(results)

            # Calcular porcentaje máximo afectado
            if total_area_ha and total_area_ha > 0:
                max_affected = max_water + max_wetland
                max_affected_pct = (max_affected / total_area_ha) * 100
                console.print(f"\n[bold]Área total: {total_area_ha:.1f} ha[/bold]")

            console.print(f"\n[bold]Resumen:[/bold]")
            console.print(f"   Máximo agua: {max_water:.1f} ha")
            console.print(f"   Máximo humedal: {max_wetland:.1f} ha")
            console.print(f"   Promedio agua: {avg_water:.1f} ha")
            console.print(f"   Promedio humedal: {avg_wetland:.1f} ha")

            if total_area_ha and total_area_ha > 0:
                console.print(f"\n[bold]Porcentaje máximo afectado:[/bold]")
                console.print(f"   Agua + Humedal: {max_affected:.1f} ha ({max_affected_pct:.1f}%)")

            # Calcular tendencia
            if len(results) >= 2:
                first = results[0]
                last = results[-1]
                water_diff = last.water_ha - first.water_ha
                wetland_diff = last.wetland_ha - first.wetland_ha

                trend_water = "SUBIENDO" if water_diff > 1 else "BAJANDO" if water_diff < -1 else "ESTABLE"
                trend_wetland = "SUBIENDO" if wetland_diff > 1 else "BAJANDO" if wetland_diff < -1 else "ESTABLE"

                console.print(f"\n[dim]Tendencia agua: {trend_water} ({water_diff:+.1f} ha)[/dim]")
                console.print(f"[dim]Tendencia humedal: {trend_wetland} ({wetland_diff:+.1f} ha)[/dim]")

        # 6. Exportar JSON si se solicitó
        if output:
            output_path = Path(output)

            analysis_result = AnalysisResult(
                partida=parcel_id,
                bbox=parcel_bbox,
                total_area_hectares=total_area_ha or 0,
                date_range=date_range,
                images_analyzed=len(results),
                results=results,
            )

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(analysis_result.model_dump_json(indent=2))

            console.print(f"\n[green]DISCO: Resultados guardados en: {output_path}[/green]")

    except SystemExit:
        # typer.Exit raise SystemExit - dejar pasar sin guardar log adicional
        raise
    except Exception:
        # Cualquier otra excepción - aún así guardar el log
        import traceback
        console.print(f"\n[red]ERROR: Error inesperado durante el análisis[/red]")
    finally:
        # 7. Siempre detener captura de log y guardar, incluso si hay excepción
        try:
            # Primero imprimir el mensaje mientras LogCapture sigue activo
            parcel_id_clean = parcel_id.replace("coords:", "coords_").replace(",", "_").replace(":", "_")
            log_filename = f"log_{parcel_id_clean}_{execution_date}_{execution_time}.log"
            log_path = Path(logs_dir) / log_filename
            if not log_path.is_absolute():
                log_path = Path.cwd() / logs_dir / log_filename

            log_capture.save(log_path)

            # Imprimir usando el print original directamente para evitar loops
            if log_capture.original_print:
                log_capture.original_print(f"\n[green]LOG: Log guardado en: {log_path}[/green]")
        except Exception:
            # Silenciar errores durante el guardado del log para no ocultar el error original
            pass
        finally:
            # Siempre restaurar console.print
            log_capture.stop()


@app.command()
def validate(
    stac: bool = typer.Option(False, "--stac", help="Validar conexión STAC"),
    arba: bool = typer.Option(False, "--arba", help="Validar conexión ARBA"),
    partida: str | None = typer.Option(None, "--partida", help="Partida para probar ARBA"),
):
    """
    Valida las conexiones a los servicios externos.

    Si no se especifica ninguna opción, valida ambas.
    """
    if not stac and not arba:
        stac = True
        arba = True

    if stac:
        console.print("[cyan]CHECK: Validando Planetary Computer STAC...[/cyan]")
        try:
            from .services.stac import StacService
            svc = StacService()
            catalog = svc._get_catalog()
            console.print(f"[green]OK Conexión STAC OK[/green]")
            console.print(f"   URL: {svc.stac_url}")
        except Exception as e:
            console.print(f"[red]ERROR: Error STAC: {e}[/red]")

    if arba:
        console.print("\n[cyan]CHECK: Validando ARBA WFS...[/cyan]")
        test_partida = partida or "4606"
        console.print(f"   Probando con partida: {test_partida}")

        try:
            from .services.arba import ArbaService
            svc = ArbaService()
            parcel = svc.get_parcel_geometry(test_partida)

            if parcel:
                console.print(f"[green]OK Conexión ARBA OK[/green]")
                console.print(f"   BBOX: {parcel.bbox}")
            else:
                console.print(f"[yellow]WARNING: Partida {test_partida} no encontrada[/yellow]")
                console.print("[dim]   La conexión funciona pero la partida no existe[/dim]")

        except Exception as e:
            console.print(f"[red]ERROR: Error ARBA: {e}[/red]")


@app.command()
def version():
    """Muestra la versión del programa."""
    from . import __version__
    console.print(f"sat-analysis v{__version__}")


def main():
    """Entry point para el CLI."""
    import sys
    try:
        app()
    except SystemExit as e:
        # Propagar el código de salida correctamente
        sys.exit(e.code if e.code is not None else 0)
    except KeyboardInterrupt:
        # Ctrl+C - salir limpiamente
        sys.exit(130)
    finally:
        # Asegurar limpieza de recursos de Rich/terminal
        try:
            console.file.close()
        except Exception:
            pass
