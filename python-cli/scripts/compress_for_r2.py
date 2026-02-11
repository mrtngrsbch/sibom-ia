#!/usr/bin/env python3
"""
compress_for_r2.py

Comprime los boletines y el índice para deployment en Cloudflare R2.
Genera archivos .gz individuales para lazy loading eficiente.

Uso:
    python compress_for_r2.py                    # Comprime todo
    python compress_for_r2.py --output dist/     # Directorio de salida personalizado
    python compress_for_r2.py --index-only       # Solo comprimir índice

@version 1.0.0
@created 2026-01-09
"""

import gzip
import json
import argparse
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()


def compress_file(src_path: Path, dest_path: Path) -> tuple[Path, int, int]:
    """
    Comprime un archivo JSON con gzip.
    Retorna: (path, tamaño_original, tamaño_comprimido)
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    original_size = src_path.stat().st_size

    with open(src_path, 'rb') as f_in:
        with gzip.open(dest_path, 'wb', compresslevel=9) as f_out:
            shutil.copyfileobj(f_in, f_out)

    compressed_size = dest_path.stat().st_size
    return (dest_path, original_size, compressed_size)


def compress_boletines(boletines_dir: Path, output_dir: Path, max_workers: int = 4) -> dict:
    """
    Comprime todos los boletines JSON en paralelo.
    """
    json_files = list(boletines_dir.glob("*.json"))

    if not json_files:
        console.print("[yellow]⚠️ No se encontraron boletines en {boletines_dir}[/yellow]")
        return {"count": 0, "original_size": 0, "compressed_size": 0}

    console.print(f"\n[bold]📦 Comprimiendo {len(json_files)} boletines...[/bold]")

    dest_dir = output_dir / "boletines"
    dest_dir.mkdir(parents=True, exist_ok=True)

    total_original = 0
    total_compressed = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Comprimiendo...", total=len(json_files))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for src in json_files:
                dest = dest_dir / f"{src.name}.gz"
                futures[executor.submit(compress_file, src, dest)] = src

            for future in as_completed(futures):
                src = futures[future]
                try:
                    _, orig_size, comp_size = future.result()
                    total_original += orig_size
                    total_compressed += comp_size
                except Exception as e:
                    console.print(f"[red]Error comprimiendo {src.name}: {e}[/red]")

                progress.advance(task)

    return {
        "count": len(json_files),
        "original_size": total_original,
        "compressed_size": total_compressed
    }


def compress_index(index_path: Path, output_dir: Path) -> dict:
    """
    Comprime el índice de normativas.
    """
    if not index_path.exists():
        console.print(f"[yellow]⚠️ Índice no encontrado: {index_path}[/yellow]")
        return {"original_size": 0, "compressed_size": 0}

    console.print(f"\n[bold]📋 Comprimiendo índice: {index_path.name}...[/bold]")

    dest_path = output_dir / f"{index_path.name}.gz"
    _, orig_size, comp_size = compress_file(index_path, dest_path)

    return {
        "original_size": orig_size,
        "compressed_size": comp_size,
        "path": dest_path
    }


def format_size(size_bytes: int) -> str:
    """Formatea bytes a formato legible."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def main():
    parser = argparse.ArgumentParser(description="Comprime datos para Cloudflare R2")
    parser.add_argument("--output", "-o", default="dist", help="Directorio de salida")
    parser.add_argument("--boletines", "-b", default="boletines", help="Directorio de boletines")
    parser.add_argument("--index", "-i", default="normativas_index_minimal.json", help="Archivo de índice")
    parser.add_argument("--index-only", action="store_true", help="Solo comprimir índice")
    parser.add_argument("--workers", "-w", type=int, default=4, help="Workers paralelos")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    console.print("[bold blue]🚀 Preparando archivos para Cloudflare R2[/bold blue]")
    console.print(f"   Salida: {output_dir.absolute()}")

    stats = {
        "boletines": {"count": 0, "original_size": 0, "compressed_size": 0},
        "index": {"original_size": 0, "compressed_size": 0}
    }

    # 1. Comprimir índice
    index_path = Path(args.index)
    stats["index"] = compress_index(index_path, output_dir)

    # 2. Comprimir boletines (si no es --index-only)
    if not args.index_only:
        boletines_dir = Path(args.boletines)
        stats["boletines"] = compress_boletines(boletines_dir, output_dir, args.workers)

    # 3. Mostrar resumen
    console.print("\n" + "=" * 60)
    console.print("[bold green]✅ COMPRESIÓN COMPLETADA[/bold green]")
    console.print("=" * 60)

    if stats["index"]["original_size"] > 0:
        ratio = (1 - stats["index"]["compressed_size"] / stats["index"]["original_size"]) * 100
        console.print(f"\n[bold]📋 Índice:[/bold]")
        console.print(f"   Original:   {format_size(stats['index']['original_size'])}")
        console.print(f"   Comprimido: {format_size(stats['index']['compressed_size'])}")
        console.print(f"   Reducción:  {ratio:.1f}%")

    if stats["boletines"]["count"] > 0:
        ratio = (1 - stats["boletines"]["compressed_size"] / stats["boletines"]["original_size"]) * 100
        console.print(f"\n[bold]📦 Boletines ({stats['boletines']['count']} archivos):[/bold]")
        console.print(f"   Original:   {format_size(stats['boletines']['original_size'])}")
        console.print(f"   Comprimido: {format_size(stats['boletines']['compressed_size'])}")
        console.print(f"   Reducción:  {ratio:.1f}%")

    total_orig = stats["index"]["original_size"] + stats["boletines"]["original_size"]
    total_comp = stats["index"]["compressed_size"] + stats["boletines"]["compressed_size"]

    if total_orig > 0:
        total_ratio = (1 - total_comp / total_orig) * 100
        console.print(f"\n[bold cyan]📊 TOTAL:[/bold cyan]")
        console.print(f"   Original:   {format_size(total_orig)}")
        console.print(f"   Comprimido: {format_size(total_comp)}")
        console.print(f"   Reducción:  {total_ratio:.1f}%")
        console.print(f"\n[dim]Archivos listos en: {output_dir.absolute()}[/dim]")

    # 4. Instrucciones de upload
    console.print("\n" + "=" * 60)
    console.print("[bold yellow]📤 SIGUIENTE PASO: Subir a R2[/bold yellow]")
    console.print("=" * 60)
    console.print("""
[dim]Opción 1: Wrangler CLI[/dim]
  npx wrangler r2 object put sibom-data/normativas_index_minimal.json.gz --file dist/normativas_index_minimal.json.gz
  npx wrangler r2 object put sibom-data/boletines/ --file dist/boletines/ --recursive

[dim]Opción 2: Dashboard R2[/dim]
  1. Ir a https://dash.cloudflare.com → R2
  2. Crear bucket "sibom-data"
  3. Subir carpeta dist/

[dim]Opción 3: rclone (recomendado para muchos archivos)[/dim]
  rclone copy dist/ r2:sibom-data/ --progress
""")


if __name__ == "__main__":
    main()
