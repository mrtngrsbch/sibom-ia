#!/usr/bin/env python3
"""
Reprocesa los PDFs de Carlos Tejedor sobrescribiendo los JSON existentes.
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.vision_extractor import extract_bulletin_with_vision
from extractors.balance_header import extract_header_with_periodo_code
from extractors.vision_extractor import extract_tables_as_markdown
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()


async def reprocess_pdf(pdf_path: Path, output_dir: Path, municipio: str = "Carlos Tejedor") -> bool:
    """Reprocesa un PDF y sobrescribe el JSON existente."""

    # Leer PDF
    pdf_content = pdf_path.read_bytes()

    # Extraer con Vision API
    result = await extract_bulletin_with_vision(
        pdf_content,
        f"file://{pdf_path}",
        municipio=municipio,
        extract_tables=True
    )

    if not result:
        return False

    title, content, quality = result

    # Extraer cabecera
    cabecera, periodo_code = extract_header_with_periodo_code(content, municipio)

    # Extraer tablas
    tablas_md = extract_tables_as_markdown(content)

    # Determinar fecha de documento
    fecha_doc = cabecera.get("fecha_generacion", "").split()[0] if cabecera.get("fecha_generacion") else "s/d"

    # Generar nombre de archivo (mismo formato que cli.py)
    url_hash = pdf_path.stem.split('_')[-1]  # Extraer hash del nombre
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f"Carlos_Tejedor_Balances_{timestamp}_{url_hash}.json"

    # Crear documento completo
    doc_data = {
        "municipio": municipio,
        "tipo_documento": "balances",
        "tipo_detalle": cabecera.get("tipo_documento", ""),
        "periodo": periodo_code or "s/d",
        "fecha_documento": fecha_doc,
        "cabecera": cabecera,
        "contenido": content,  # CRÍTICO: texto completo
        "url_origen": f"file://{pdf_path}",
        "titulo_extraido": title,
        "status": "completed",
        "tablas_md": tablas_md,
        "calidad": quality,
        "pdf_file": str(pdf_path),
        "json_file": output_file.name,
        "metadata": {
            "fecha_scraping": datetime.now().isoformat(),
            "version_scraper": "3.2",
            "source_type": "transparency_vision"
        }
    }

    # Guardar JSON
    with output_file.open('w', encoding='utf-8') as f:
        json.dump(doc_data, f, indent=2, ensure_ascii=False)

    # Actualizar SQLite
    try:
        from utils.sqlite_manager import get_sqlite_manager
        mgr = get_sqlite_manager()
        mgr.insert_transparency_doc(doc_data)
    except Exception as sqlite_err:
        pass  # No fallar si SQLite falla

    return True


async def main():
    pdf_dir = Path("boletines/Carlos_Tejedor/pdfs")
    output_dir = Path("boletines/Carlos_Tejedor")

    if not pdf_dir.exists():
        console.print(f"[red]No existe: {pdf_dir}[/red]")
        return

    pdf_files = sorted(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        console.print("[red]No hay PDFs[/red]")
        return

    console.print(f"[cyan]{len(pdf_files)} PDFs a reprocesar[/cyan]\n")

    stats = {"success": 0, "error": 0, "with_header": 0}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:

        task = progress.add_task("[cyan]Extrayendo...", total=len(pdf_files))

        for pdf_file in pdf_files:
            progress.update(task, description=f"[cyan]{pdf_file.name[:30]}...[/cyan]")

            try:
                success = await reprocess_pdf(pdf_file, output_dir)
                if success:
                    stats["success"] += 1
                    # Verificar si tiene cabecera
                    # (no podemos acceder al JSON recién creado fácilmente, asumimos éxito)
                else:
                    stats["error"] += 1
            except Exception as e:
                console.print(f"\n[red]Error con {pdf_file.name}: {e}[/red]")
                stats["error"] += 1

            progress.advance(task)

    console.print(f"\n[bold]Resumen:[/bold]")
    console.print(f"  ✓ Exitosos: {stats['success']}")
    console.print(f"  ✗ Errores: {stats['error']}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Reprocesar PDFs de Carlos Tejedor')
    parser.add_argument('--limit', '-l', type=int, default=0, help='Limitar a N PDFs (0 = todos)')
    parser.add_argument('--resume', '-r', action='store_true', help='Continuar desde donde se dejó (salta PDFs con JSON válido)')
    args = parser.parse_args()

    def get_processed_hashes(output_dir: Path) -> set[str]:
        """Retorna hashes de PDFs que ya tienen JSON válido (con contenido)."""
        processed = set()
        for json_file in output_dir.glob("Carlos_Tejedor_Balances_*.json"):
            try:
                with json_file.open('r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Solo considerar válido si tiene contenido con longitud > 1000
                    if data.get('contenido') and len(data.get('contenido', '')) > 1000:
                        # Extraer hash del nombre: ..._timestamp_HASH.json
                        hash_part = json_file.stem.split('_')[-1]
                        processed.add(hash_part)
            except Exception:
                pass  # JSON corrupto o inválido, se reprocesará
        return processed

    # Modificar main para aceptar limit y resume
    async def main_with_limit():
        pdf_dir = Path("boletines/Carlos_Tejedor/pdfs")
        output_dir = Path("boletines/Carlos_Tejedor")

        if not pdf_dir.exists():
            console.print(f"[red]No existe: {pdf_dir}[/red]")
            return

        pdf_files = sorted(pdf_dir.glob("*.pdf"))

        if not pdf_files:
            console.print("[red]No hay PDFs[/red]")
            return

        # Aplicar resume si se especificó
        if args.resume:
            processed_hashes = get_processed_hashes(output_dir)
            original_count = len(pdf_files)
            # Filtrar PDFs: extraer hash del nombre y saltar si está procesado
            pdf_files = [p for p in pdf_files if p.stem.split('_')[-1] not in processed_hashes]
            skipped = original_count - len(pdf_files)
            if skipped > 0:
                console.print(f"[green]Resume: {skipped} PDFs ya procesados, saltando...[/green]\n")
            if not pdf_files:
                console.print("[green]✓ Todos los PDFs ya están procesados[/green]")
                return

        # Aplicar límite si se especificó
        if args.limit > 0:
            pdf_files = pdf_files[:args.limit]
            console.print(f"[yellow]Limitando a {args.limit} PDFs[/yellow]\n")

        console.print(f"[cyan]{len(pdf_files)} PDFs a reprocesar[/cyan]\n")

        stats = {"success": 0, "error": 0}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:

            task = progress.add_task("[cyan]Extrayendo...", total=len(pdf_files))

            for pdf_file in pdf_files:
                progress.update(task, description=f"[cyan]{pdf_file.name[:30]}...[/cyan]")

                try:
                    success = await reprocess_pdf(pdf_file, output_dir)
                    if success:
                        stats["success"] += 1
                    else:
                        stats["error"] += 1
                except Exception as e:
                    console.print(f"\n[red]Error con {pdf_file.name}: {e}[/red]")
                    stats["error"] += 1

                progress.advance(task)

        console.print(f"\n[bold]Resumen:[/bold]")
        console.print(f"  ✓ Exitosos: {stats['success']}")
        console.print(f"  ✗ Errores: {stats['error']}")

    asyncio.run(main_with_limit())
