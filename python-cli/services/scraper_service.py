#!/usr/bin/env python3
"""
services/scraper_service.py

Servicio de orquestación del scraping.

Coordina la descarga de PDFs, extracción de contenido, guardado de archivos
y tracking de progreso.

@version 2.0.0
@created 2026-02-02
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import httpx
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeRemainingColumn,
)

from utils.state_tracker import StateTracker
from services.pdf_processor import PDFProcessor

console = Console()


class ScrapingResult:
    """Resultado de una operación de scraping."""

    def __init__(self):
        self.processed = 0
        self.errors = 0
        self.skipped = 0
        self.total_size_mb = 0
        self.start_time = datetime.now()
        self.end_time = None

    def finish(self):
        """Marca el fin del scraping."""
        self.end_time = datetime.now()

    @property
    def duration(self) -> float:
        """Retorna la duración en segundos."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Retorna el resultado como diccionario."""
        return {
            "processed": self.processed,
            "errors": self.errors,
            "skipped": self.skipped,
            "total_size_mb": self.total_size_mb,
            "duration_seconds": self.duration,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None
        }


class ScraperService:
    """
    Servicio de orquestación del scraping.

    Responsabilidades:
    - Descargar PDFs desde URLs
    - Coordinar extracción de contenido
    - Guardar PDFs y JSONs
    - Actualizar estado del procesamiento
    - Generar reportes
    """

    def __init__(
        self,
        municipio: str,
        categoria: str,
        output_dir: Path = None,
        save_pdfs: bool = True,
        tracker: StateTracker = None,
        processor: PDFProcessor = None
    ):
        """
        Inicializa el servicio de scraping.

        Args:
            municipio: Nombre del municipio
            categoria: Categoría (balances, presupuestos, etc.)
            output_dir: Directorio de salida (por defecto: boletines/{municipio}/)
            save_pdfs: Si True, guarda PDFs originales
            tracker: StateTracker (se crea uno nuevo si no se proporciona)
            processor: PDFProcessor (se crea uno nuevo si no se proporciona)
        """
        self.municipio = municipio
        self.categoria = categoria
        self.save_pdfs = save_pdfs

        # Crear tracker
        if tracker is None:
            from config import BOLETINES_DIR
            municipio_slug = municipio.lower().replace(" ", "_")
            output_dir = output_dir or BOLETINES_DIR / municipio_slug

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.tracker = tracker or StateTracker(municipio, categoria, self.output_dir)
        self.processor = processor or PDFProcessor()

    async def download_pdf(self, url: str, timeout: int = 60) -> Optional[bytes]:
        """
        Descarga un PDF desde una URL.

        Args:
            url: URL del PDF
            timeout: Timeout en segundos

        Returns:
            Contenido binario del PDF o None si falla
        """
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
        except Exception as e:
            console.print(f"[red]Error descargando {url[:50]}...: {e}[/red]")
            return None

    async def process_url(
        self,
        url: str,
        is_table: bool = True
    ) -> Dict[str, Any]:
        """
        Procesa una URL completa: descarga, extrae, guarda.

        Args:
            url: URL del PDF
            is_table: Si True, usa extracción optimizada para tablas

        Returns:
            Diccionario con resultado:
            - success: True si fue exitoso
            - pdf_path: Ruta al PDF guardado
            - json_path: Ruta al JSON guardado
            - error: Mensaje de error si falló
        """
        result = {
            "success": False,
            "pdf_path": "",
            "json_path": "",
            "error": ""
        }

        # 1. Descargar PDF
        pdf_content = await self.download_pdf(url)
        if not pdf_content:
            result["error"] = "No se pudo descargar el PDF"
            return result

        size_mb = len(pdf_content) / (1024 * 1024)

        # 2. Guardar PDF si se solicita
        pdf_path = ""
        if self.save_pdfs:
            filename = url.split('/')[-1]
            pdf_path = self.processor.save_pdf(pdf_content, self.output_dir, filename)
            result["pdf_path"] = str(pdf_path)

        # 3. Extraer contenido
        try:
            titulo, contenido, metadata = await self.processor.process_pdf(
                pdf_content=pdf_content,
                url=url,
                municipio=self.municipio,
                extract_tables=is_table
            )

            # Agregar ruta del PDF a metadata
            if pdf_path:
                metadata["pdf_path"] = str(pdf_path)

            # 4. Guardar JSON
            tipo_doc = self.categoria.capitalize()
            json_path = self.processor.save_json(
                titulo=titulo,
                contenido=contenido,
                metadata=metadata,
                municipio=self.municipio,
                tipo_documento=tipo_doc,
                output_dir=self.output_dir
            )

            result["success"] = True
            result["json_path"] = str(json_path)

        except Exception as e:
            result["error"] = str(e)
            console.print(f"[red]Error extrayendo {url[:50]}...: {e}[/red]")

        return result

    async def scrape_urls(
        self,
        urls: List[str],
        is_table: bool = True,
        limit: int = 0,
        resume: bool = False
    ) -> ScrapingResult:
        """
        Scrapea una lista de URLs.

        Args:
            urls: Lista de URLs a procesar
            is_table: Si True, usa extracción optimizada para tablas
            limit: Límite de URLs a procesar (0 = todas)
            resume: Si True, salta las ya procesadas

        Returns:
            ScrapingResult con estadísticas
        """
        result = ScrapingResult()

        # Filtrar URLs si es resume
        if resume:
            pending_urls = [u for u in urls if not self.tracker.is_processed(u)]
            console.print(f"[yellow]Modo resume: {len(pending_urls)} URLs pendientes de {len(urls)}[/yellow]")
            urls = pending_urls

        # Aplicar límite
        if limit > 0:
            urls = urls[:limit]

        total = len(urls)
        if total == 0:
            console.print("[yellow]No hay URLs para procesar[/yellow]")
            result.finish()
            return result

        # Procesar con barra de progreso
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:

            task = progress.add_task(
                f"[cyan]Scrapeando {total} PDFs...[/cyan]",
                total=total
            )

            for i, url in enumerate(urls):
                # Nombre de archivo para mostrar
                filename = url.split('/')[-1][:40]
                progress.update(task, description=f"[cyan]{filename}[/cyan]")

                # Verificar si ya fue procesado (doble check)
                if resume and self.tracker.is_processed(url):
                    progress.update(task, advance=1)
                    continue

                # Procesar URL
                process_result = await self.process_url(url, is_table)

                # Actualizar tracker según resultado
                if process_result["success"]:
                    self.tracker.mark_processed(
                        url=url,
                        pdf_path=process_result["pdf_path"],
                        json_path=process_result["json_path"]
                    )
                    result.processed += 1
                    result.total_size_mb += len(await self.download_pdf(url)) / (1024 * 1024) if process_result["pdf_path"] else 0
                else:
                    self.tracker.mark_error(url, process_result["error"])
                    result.errors += 1

                progress.update(task, advance=1)

        result.finish()

        # Generar reporte Markdown
        self.tracker.save_markdown_report()

        return result

    def print_final_report(self, result: ScrapingResult):
        """Imprime el reporte final del scraping."""
        console.print("\n[bold green]╔════════════════════════════════════════╗[/bold green]")
        console.print("[bold green]║      SCRAPING COMPLETADO               ║[/bold green]")
        console.print("[bold green]╚════════════════════════════════════════╝[/bold green]\n")

        console.print(f"[cyan]Municipio:[/cyan] {self.municipio}")
        console.print(f"[cyan]Categoría:[/cyan] {self.categoria}")
        console.print(f"[cyan]Duración:[/cyan] {result.duration:.1f} segundos")
        console.print()

        console.print(f"[green]✅ Procesados:[/green] {result.processed}")
        console.print(f"[red]❌ Errores:[/red] {result.errors}")
        console.print(f"[yellow]⊘ Saltados:[/yellow] {result.skipped}")
        console.print()

        if self.save_pdfs:
            size_str = f"{result.total_size_mb:.1f} MB" if result.total_size_mb > 0 else "N/A"
            console.print(f"[cyan]📁 PDFs guardados:[/cyan] {self.output_dir / 'pdfs'}")
            console.print(f"[cyan]📊 Tamaño total:[/cyan] {size_str}")

        console.print()
        console.print(f"[dim]Estado guardado: {self.tracker.state_file}[/dim]")
        console.print(f"[dim]Reporte: {self.output_dir / '_procesamiento.md'}[/dim]")


async def scrape(
    municipio: str,
    categoria: str,
    urls: List[str] = None,
    save_pdfs: bool = True,
    is_table: bool = True,
    limit: int = 0,
    resume: bool = False,
    test_mode: bool = False
) -> ScrapingResult:
    """
    Función de alto nivel para scraping.

    Args:
        municipio: Nombre del municipio
        categoria: Categoría (balances, presupuestos, etc.)
        urls: Lista de URLs (si None, se obtienen de sources_user.yaml)
        save_pdfs: Si True, guarda PDFs originales
        is_table: Si True, usa extracción optimizada para tablas
        limit: Límite de PDFs a procesar
        resume: Si True, retoma donde se quedó
        test_mode: Si True, usa directorio de prueba

    Returns:
        ScrapingResult con estadísticas
    """
    # Obtener URLs si no se proporcionan
    if urls is None:
        # Importar aquí para evitar dependencias circulares
        import yaml
        from config import USER_SOURCES_FILE, SOURCES_FILE, BOLETINES_DIR

        sources_file = USER_SOURCES_FILE if USER_SOURCES_FILE.exists() else SOURCES_FILE

        if not sources_file.exists():
            console.print(f"[red]Error: No se encontró {sources_file.name}[/red]")
            return ScrapingResult()

        with sources_file.open('r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # Buscar fuentes que coincidan con el municipio y categoría
        urls = []
        # Intentar múltiples variantes del nombre del municipio
        municipio_variants = [
            municipio.lower(),  # "carlos tejedor"
            municipio.lower().replace(" ", "_"),  # "carlos_tejedor"
            municipio.replace(" ", "_").lower(),  # "carlos_tejedor"
        ]

        for source in config_data.get('sources', []):
            source_name = source.get('name', '')
            source_categories = source.get('categories', [])

            # Verificar si coincide con el municipio Y la categoría
            municipio_matches = any(m in source_name.lower() for m in municipio_variants)

            # Verificar si la categoría coincide o si no hay categorías definidas
            category_matches = (not source_categories) or (categoria in source_categories)

            if municipio_matches and category_matches:
                url_patterns = source.get('url_patterns', [])
                urls.extend(url_patterns)

        if not urls:
            console.print(f"[yellow]No se encontraron URLs para {municipio} / {categoria}[/yellow]")
            console.print(f"[yellow]Revisa {sources_file.name}[/yellow]")
            return ScrapingResult()

    # Determinar directorio de salida
    output_dir = None
    if test_mode:
        from config import BOLETINES_DIR
        output_dir = BOLETINES_DIR / f"{municipio.replace(' ', '_')}_test"

    # Crear servicio
    service = ScraperService(
        municipio=municipio,
        categoria=categoria,
        output_dir=output_dir,
        save_pdfs=save_pdfs
    )

    # Ejecutar scraping
    result = await service.scrape_urls(
        urls=urls,
        is_table=is_table,
        limit=limit,
        resume=resume
    )

    # Imprimir reporte
    service.print_final_report(result)

    return result


def get_scraper_service(
    municipio: str,
    categoria: str,
    save_pdfs: bool = True
) -> ScraperService:
    """
    Obtiene una instancia de ScraperService.

    Args:
        municipio: Nombre del municipio
        categoria: Categoría
        save_pdfs: Si True, guarda PDFs

    Returns:
        ScraperService instance
    """
    return ScraperService(
        municipio=municipio,
        categoria=categoria,
        save_pdfs=save_pdfs
    )
