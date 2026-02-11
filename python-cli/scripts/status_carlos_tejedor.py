#!/usr/bin/env python3
"""
Script de Estado del Scraping - Carlos Tejedor Transparency

Muestra el estado completo del scraping de documentos de transparencia:
- PDFs descubiertos por categoría
- PDFs procesados exitosamente
- PDFs pendientes
- Estadísticas de calidad de extracción
- Uso de rate limit de Vision API

Uso:
    cd python-cli
    python scripts/status_carlos_tejedor.py

@version 1.0.0
@created 2026-01-30
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TaskProgressColumn

# Imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import BOLETINES_DIR, USER_SOURCES_FILE, SOURCES_FILE
import yaml

console = Console()


def load_sources():
    """Carga las fuentes desde sources_user.yaml o sources.yaml"""
    sources_file = USER_SOURCES_FILE if USER_SOURCES_FILE.exists() else SOURCES_FILE
    with sources_file.open('r', encoding='utf-8') as f:
        return yaml.safe_load(f).get('sources', [])


def load_progress(category: str, municipio: str = "Carlos Tejedor") -> set:
    """Carga el progreso de una categoría"""
    municipio_slug = municipio.replace(' ', '_')
    progress_file = BOLETINES_DIR / municipio_slug / f".{category}_progress.json"

    if progress_file.exists():
        with progress_file.open('r') as f:
            return set(json.load(f))
    return set()


def get_processed_files(municipio: str = "Carlos Tejedor"):
    """Obtiene todos los JSON procesados"""
    municipio_slug = municipio.replace(' ', '_')
    output_dir = BOLETINES_DIR / municipio_slug

    if not output_dir.exists():
        return []

    files = []
    for json_file in output_dir.glob("*.json"):
        if json_file.name.startswith('.'):
            continue

        try:
            with json_file.open('r') as f:
                data = json.load(f)
                files.append({
                    'file': json_file,
                    'name': json_file.name,
                    'category': data.get('tipo_documento', 'unknown'),
                    'url': data.get('url_origen', ''),
                    'title': data.get('titulo_extraido', ''),
                    'status': data.get('status', 'unknown'),
                    'quality': data.get('calidad', {}).get('confidence', 0),
                    'pages': data.get('calidad', {}).get('pages_processed', 0),
                    'tables': len(data.get('tablas_md', [])),
                    'date': data.get('metadata', {}).get('fecha_scraping', '')
                })
        except Exception as e:
            console.print(f"[yellow]Error leyendo {json_file.name}: {e}[/yellow]")

    return files


def get_rate_limit_status():
    """Obtiene el estado del rate limit de Vision API"""
    try:
        from utils.vision_rate_limiter import get_rate_limiter
        limiter = get_rate_limiter()
        stats = limiter.get_stats()
        return stats
    except Exception:
        return None


def print_status_summary():
    """Imprime el resumen de estado"""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Carlos Tejedor Transparency - Estado del Scraping[/bold cyan]",
        border_style="cyan"
    ))
    console.print()

    # 1. Categorías descubiertas
    sources = load_sources()
    categories_found = {}

    for source in sources:
        if 'Carlos Tejedor' in source.get('name', ''):
            cats = source.get('categories', ['general'])
            url_count = len(source.get('url_patterns', []))
            enabled = source.get('enabled', False)

            for cat in cats:
                if cat not in categories_found:
                    categories_found[cat] = {'total': 0, 'enabled': False}
                categories_found[cat]['total'] += url_count
                if enabled:
                    categories_found[cat]['enabled'] = True

    # Tabla de categorías descubiertas
    console.print("[bold]Categorías Descubiertas:[/bold]")
    cat_table = Table(show_header=True, header_style="bold cyan")
    cat_table.add_column("Categoría", style="cyan")
    cat_table.add_column("PDFs", justify="right", style="green")
    cat_table.add_column("Estado", justify="center")

    for cat, data in sorted(categories_found.items()):
        status = "✓ Habilitado" if data['enabled'] else "— Deshabilitado"
        cat_table.add_row(cat.capitalize(), str(data['total']), status)

    console.print(cat_table)
    console.print()

    # 2. Estado de procesamiento por categoría
    console.print("[bold]Estado de Procesamiento:[/bold]")
    status_table = Table(show_header=True, header_style="bold cyan")
    status_table.add_column("Categoría", style="cyan")
    status_table.add_column("Procesados", justify="right", style="green")
    status_table.add_column("Pendientes", justify="right", style="yellow")
    status_table.add_column("Progreso", justify="right")
    status_table.add_column("Barra")

    total_processed = 0
    total_pending = 0

    for cat, data in sorted(categories_found.items()):
        processed = load_progress(cat)
        processed_count = len(processed)
        pending = max(0, data['total'] - processed_count)

        total_processed += processed_count
        total_pending += pending

        percent = (processed_count / data['total'] * 100) if data['total'] > 0 else 0
        bar_length = int(percent / 5)
        bar = "█" * bar_length + "░" * (20 - bar_length)

        status_table.add_row(
            cat.capitalize(),
            str(processed_count),
            str(pending),
            f"{percent:.1f}%",
            f"[{bar}]"
        )

    console.print(status_table)
    console.print()

    # 3. Archivos procesados
    processed_files = get_processed_files()
    if processed_files:
        console.print("[bold]Archivos Procesados:[/bold]")
        files_table = Table(show_header=True, header_style="bold cyan")
        files_table.add_column("Archivo", style="cyan")
        files_table.add_column("Categoría")
        files_table.add_column("Calidad", justify="right")
        files_table.add_column("Tablas", justify="right")
        files_table.add_column("Páginas", justify="right")
        files_table.add_column("Fecha")

        for f in sorted(processed_files, key=lambda x: x['date'], reverse=True)[:10]:  # Últimos 10
            quality_str = f"{f['quality']:.0%}" if f['quality'] > 0 else "N/A"
            date_str = f['date'][:10] if f['date'] else "N/A"
            files_table.add_row(
                f['name'][:40] + "..." if len(f['name']) > 40 else f['name'],
                f['category'],
                quality_str,
                str(f['tables']),
                str(f['pages']),
                date_str
            )

        console.print(files_table)
        console.print()

    # 4. Rate limit Vision API
    rate_stats = get_rate_limit_status()
    if rate_stats:
        console.print("[bold]Rate Limit - Vision API:[/bold]")

        today = rate_stats.get('today', 0)
        limit = rate_stats.get('limit', 1000)
        remaining = limit - today
        percent = (today / limit * 100)

        bar_length = int(percent / 5)
        bar_color = "green" if percent < 70 else "yellow" if percent < 90 else "red"
        bar = "█" * bar_length + "░" * (20 - bar_length)

        console.print(f"  Usado hoy: [bold]{today}[/bold] / {limit}")
        console.print(f"  Restante: [{bar_color}]{remaining}[/{bar_color}]")
        console.print(f"  [{bar_color}][{bar}][/{bar_color}] {percent:.1f}%")

        if today >= limit:
            console.print("\n  [red]⚠️ Límite diario alcanzado[/red]")
            console.print("  [yellow]💡 Intenta de nuevo mañana o usa otra API key[/yellow]")
        console.print()

    # 5. Resumen general
    console.print(Panel.fit(
        f"[bold]Resumen:[/bold]\n"
        f"  Total PDFs descubiertos: {sum(c['total'] for c in categories_found.values())}\n"
        f"  ✓ PDFs procesados: {total_processed}\n"
        f"  ⊗ PDFs pendientes: {total_pending}\n"
        f"  Progreso global: {total_processed / max(1, sum(c['total'] for c in categories_found.values())) * 100:.1f}%",
        title="Estado General",
        border_style="green"
    ))


def print_pending_pdfs(category: str = "balances"):
    """Muestra los PDFs pendientes de procesar"""
    sources = load_sources()

    for source in sources:
        if 'Carlos Tejedor' in source.get('name', '') and category in source.get('categories', []):
            urls = source.get('url_patterns', [])
            processed = load_progress(category)
            pending = [u for u in urls if u not in processed]

            console.print(f"\n[bold]PDFs Pendientes - {category.capitalize()}:[/bold]")
            console.print(f"  Pendientes: {len(pending)} de {len(urls)}")
            console.print()

            for i, url in enumerate(pending[:20], 1):  # Primeros 20
                filename = url.split('/')[-1]
                console.print(f"  {i:2d}. {filename}")

            if len(pending) > 20:
                console.print(f"  ... y {len(pending) - 20} más")

            break


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Estado del scraping - Carlos Tejedor Transparency"
    )
    parser.add_argument(
        '--pending',
        metavar='CATEGORIA',
        help='Mostrar PDFs pendientes de una categoría'
    )

    args = parser.parse_args()

    if args.pending:
        print_pending_pdfs(args.pending)
    else:
        print_status_summary()


if __name__ == "__main__":
    main()
