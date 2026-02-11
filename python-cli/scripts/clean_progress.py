#!/usr/bin/env python3
"""
Limpia el archivo de progreso de scraping.

Analiza los JSONs existentes y reconstruye el archivo de progreso
solo con URLs que tienen contenido válido (> 1000 caracteres).

Uso:
    python scripts/clean_progress.py --municipio "Carlos Tejedor" --category balances
"""
import argparse
import json
import sys
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

sys.path.insert(0, str(Path(__file__).parent.parent))

console = Console()


def clean_progress(municipio: str, category: str, dry_run: bool = False) -> None:
    """Limpia el archivo de progreso basado en JSONs válidos."""

    # Normalizar nombres
    # Para archivos JSON: mantener mayúsculas del municipio (Carlos_Tejedor)
    municipio_prefix = municipio.replace(" ", "_")  # Carlos_Tejedor
    category_clean = category.lower()

    # Directorios - buscar iterando para evitar problemas de encoding
    boletines_dir = Path("boletines")
    output_dir = None

    for item in boletines_dir.iterdir():
        if item.is_dir() and municipio.replace(" ", "_") in item.name or municipio in item.name:
            output_dir = item
            break

    if output_dir is None:
        console.print(f"[red]No existe directorio para: {municipio}[/red]")
        console.print("[dim]Directorios disponibles en boletines/:[/dim]")
        for item in boletines_dir.iterdir():
            if item.is_dir():
                console.print(f"  - {item.name}")
        return

    progress_file = output_dir / f".{category_clean}_progress.json"

    # Buscar JSONs (usando el prefijo con mayúsculas preservadas)
    json_files = sorted(output_dir.glob(f"{municipio_prefix}_{category.capitalize()}_*.json"))

    if not json_files:
        console.print(f"[yellow]No se encontraron JSONs para {municipio} / {category}[/yellow]")
        return

    console.print(f"[cyan]Analizando {len(json_files)} JSONs...[/cyan]\n")

    # Analizar JSONs
    valid_urls = []
    invalid_count = 0
    total_chars = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Analizando...", total=len(json_files))

        for json_file in json_files:
            try:
                with json_file.open('r', encoding='utf-8') as f:
                    data = json.load(f)

                contenido_len = len(data.get('contenido', ''))
                url = data.get('url_origen', '')

                if contenido_len > 1000 and url:
                    valid_urls.append(url)
                    total_chars += contenido_len
                else:
                    invalid_count += 1

            except Exception as e:
                console.print(f"[yellow]Error leyendo {json_file.name}: {e}[/yellow]")
                invalid_count += 1

            progress.advance(task)

    # Mostrar resultados
    console.print()
    console.print(f"[bold]Resultados:[/bold]")
    console.print(f"  JSONs analizados: {len(json_files)}")
    console.print(f"  Válidos (contenido > 1000): [green]{len(valid_urls)}[/green]")
    console.print(f"  Inválidos (vacíos/cortos): [red]{invalid_count}[/red]")
    console.print(f"  Total caracteres válidos: {total_chars:,}")
    console.print()

    # Guardar progreso limpio
    if dry_run:
        console.print("[yellow]Modo dry-run: no se guardan cambios[/yellow]")
        console.print(f"[dim]URLs válidas: {len(valid_urls)}[/dim]")
        return

    # Backup del archivo original
    if progress_file.exists():
        backup_file = progress_file.with_suffix('.json.broken')
        console.print(f"[dim]Backup: {backup_file.name}[/dim]")
        progress_file.rename(backup_file)

    # Guardar progreso limpio
    with progress_file.open('w', encoding='utf-8') as f:
        json.dump(valid_urls, f, indent=2)

    console.print(f"[green]✓ Progreso guardado: {progress_file.name}[/green]")
    console.print(f"[dim]URLs válidas guardadas: {len(valid_urls)}[/dim]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Limpiar progreso de scraping')
    parser.add_argument('--municipio', '-m', required=True, help='Nombre del municipio')
    parser.add_argument('--category', '-c', required=True,
                       choices=['balances', 'presupuestos', 'licitaciones', 'concursos'],
                       help='Categoría de documento')
    parser.add_argument('--dry-run', '-d', action='store_true',
                       help='Solo analizar, no guardar cambios')
    args = parser.parse_args()

    clean_progress(args.municipio, args.category, args.dry_run)
