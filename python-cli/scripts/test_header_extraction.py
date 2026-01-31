#!/usr/bin/env python3
"""
Test del extractor de cabeceras con PDFs ya descargados.

Reprocesa un PDF local para verificar que la extracción de cabecera funciona.
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.vision_extractor import extract_bulletin_with_vision
from extractors.balance_header import extract_header_with_periodo_code
from rich.console import Console

console = Console()


async def test_with_local_pdf():
    """Prueba el extractor con un PDF local."""

    # Buscar un PDF local
    pdf_dir = Path("boletines/Carlos_Tejedor/pdfs")

    if not pdf_dir.exists():
        console.print(f"[red]No existe directorio: {pdf_dir}[/red]")
        return

    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        console.print("[red]No hay PDFs en el directorio[/red]")
        return

    # Usar el primer PDF
    pdf_file = pdf_files[0]
    console.print(f"[cyan]Probando con: {pdf_file.name}[/cyan]\n")

    # Leer el PDF
    pdf_content = pdf_file.read_bytes()

    # Extraer con Vision API
    console.print("[yellow]Extrayendo con Vision API...[/yellow]")
    result = await extract_bulletin_with_vision(
        pdf_content,
        f"file://{pdf_file}",
        municipio="Carlos Tejedor",
        extract_tables=True
    )

    if not result:
        console.print("[red]Fallo la extracción[/red]")
        return

    title, content, quality = result

    console.print(f"[green]✓ Extracción completada[/green]")
    console.print(f"  Título: {title[:80]}...")
    console.print(f"  Longitud: {len(content):,} caracteres")
    console.print(f"  Calidad: {quality['confidence']:.1%}\n")

    # Extraer cabecera
    console.print("[yellow]Extrayendo cabecera...[/yellow]")
    cabecera, periodo_code = extract_header_with_periodo_code(content, "Carlos Tejedor")

    console.print("[bold]Datos de cabecera:[/bold]")
    for key, value in cabecera.items():
        if value:
            console.print(f"  [cyan]{key}:[/cyan] {value}")
        else:
            console.print(f"  [dim]{key}:[/dim] (no extraído)")

    console.print(f"\n[bold]Periodo calculado:[/bold] {periodo_code or 'N/A'}")

    # Guardar resultado con cabecera
    output_file = Path("data/cache/test_header_extraction.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    test_data = {
        "pdf_file": str(pdf_file),
        "titulo_extraido": title,
        "cabecera": cabecera,
        "periodo_calculado": periodo_code,
        "calidad": quality
    }

    with output_file.open('w') as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)

    console.print(f"\n[green]✓ Resultado guardado en: {output_file}[/green]")


if __name__ == "__main__":
    asyncio.run(test_with_local_pdf())
