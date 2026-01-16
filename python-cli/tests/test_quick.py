#!/usr/bin/env python3
"""Test rápido - solo primeras 10 normas"""

import os
import sys
import json
from dotenv import load_dotenv
from sibom_scraper import SIBOMScraper
from rich.console import Console
from pathlib import Path

load_dotenv()
console = Console()

# Verificar API key
api_key = os.getenv('OPENROUTER_API_KEY')
if not api_key:
    console.print("[red]Error: OPENROUTER_API_KEY no encontrada[/red]")
    sys.exit(1)

# Limpiar archivos previos
output_dir = Path("boletines")
test_file = output_dir / "Test_Quick.json"
progress_file = output_dir / ".progress_test_quick.json"

if test_file.exists():
    test_file.unlink()
if progress_file.exists():
    progress_file.unlink()

console.print("[cyan]Test rápido: 10 normas del boletín 1636[/cyan]\n")

# Crear boletín de prueba con solo primeras 10 normas
scraper = SIBOMScraper(api_key, model='google/gemini-3-flash-preview')

# Simular boletín pequeño
bulletin = {
    'number': 'Test Quick',
    'date': '2024-01-10',
    'description': 'Test Quick de Alberti',
    'link': '/bulletins/1636'
}

try:
    # Fetch HTML del boletín
    base_url = "https://sibom.slyt.gba.gob.ar"
    bulletin_url = f"{base_url}{bulletin['link']}"
    bulletin_html = scraper.fetch_html(bulletin_url)

    # Extraer metadatos de normas
    normas_metadata = scraper.parse_bulletin_content_links(bulletin_html)

    # Limitar a primeras 10
    normas_metadata = normas_metadata[:10]

    console.print(f"[green]✓ Procesando {len(normas_metadata)} normas...[/green]\n")

    # Scrapear cada norma
    municipio = "Alberti"
    normas_completas = []

    for i, norma_meta in enumerate(normas_metadata, 1):
        console.print(f"[dim]{i}/10: {norma_meta['titulo'][:50]}...[/dim]")
        norma_completa = scraper._scrape_individual_norm(norma_meta, base_url, municipio)
        normas_completas.append(norma_completa)

    # Construir resultado
    result = {
        "municipio": municipio,
        "numero_boletin": "Test Quick",
        "fecha_boletin": "2024-01-10",
        "boletin_url": bulletin_url,
        "status": "completed",
        "total_normas": len(normas_completas),
        "normas": normas_completas,
        "metadata_boletin": {
            "total_caracteres": sum(n['metadata'].get('longitud_caracteres', 0) for n in normas_completas),
            "total_tablas": sum(n['metadata'].get('total_tablas', 0) for n in normas_completas),
            "total_montos": sum(n['metadata'].get('total_montos', 0) for n in normas_completas),
        }
    }

    # Guardar
    with test_file.open('w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    console.print(f"\n[bold green]✓ TEST COMPLETADO[/bold green]")
    console.print(f"\nArchivo guardado: {test_file}")
    console.print(f"Total normas: {result['total_normas']}")
    console.print(f"Total tablas: {result['metadata_boletin']['total_tablas']}")
    console.print(f"Total montos: {result['metadata_boletin']['total_montos']}")

    console.print(f"\n[cyan]Primeras 3 normas:[/cyan]")
    for i, norma in enumerate(result['normas'][:3], 1):
        console.print(f"\n{i}. {norma['titulo']}")
        console.print(f"   URL: {norma['url']}")
        console.print(f"   Tipo: {norma['tipo']} | Número: {norma['numero']}")
        console.print(f"   Contenido: {len(norma.get('contenido', ''))} caracteres")
        console.print(f"   Tablas: {norma['metadata'].get('total_tablas', 0)}")
        console.print(f"   Montos: {norma['metadata'].get('total_montos', 0)}")

except Exception as e:
    console.print(f"\n[red]Error: {e}[/red]")
    import traceback
    traceback.print_exc()
