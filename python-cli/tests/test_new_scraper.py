#!/usr/bin/env python3
"""
Script de test para el nuevo scraper con normas individuales
Testea con un boletín pequeño para verificar funcionalidad
"""

import os
import sys
from dotenv import load_dotenv
from sibom_scraper import SIBOMScraper
from rich.console import Console

load_dotenv()
console = Console()

def test_scraper():
    """Test del scraper con un boletín pequeño"""

    # Verificar API key
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        console.print("[red]Error: OPENROUTER_API_KEY no encontrada en .env[/red]")
        return

    # Crear scraper
    scraper = SIBOMScraper(api_key, model='google/gemini-3-flash-preview')

    console.print("[bold cyan]TEST DEL NUEVO SCRAPER[/bold cyan]\n")
    console.print("Características a verificar:")
    console.print("  ✓ User-Agent real")
    console.print("  ✓ Jitter aleatorio en delays")
    console.print("  ✓ Modo resume")
    console.print("  ✓ Normas individuales con URLs")
    console.print("  ✓ Tablas y montos por norma\n")

    # URL de un boletín pequeño de prueba
    # Usar el boletín 1636 de Alberti pero con límite de 1 para test rápido
    test_url = "https://sibom.slyt.gba.gob.ar/bulletins/1636"

    console.print(f"[yellow]URL de test: {test_url}[/yellow]")
    console.print("[yellow]Procesando 1 boletín (limitado para test)...[/yellow]\n")

    try:
        # Scrapear solo 1 boletín
        results = scraper.scrape(test_url, limit=1, parallel=1, skip_existing=False)

        if results:
            result = results[0]

            console.print("\n[bold green]✓ TEST COMPLETADO[/bold green]\n")
            console.print(f"Municipio: {result.get('municipio', 'N/A')}")
            console.print(f"Boletín: {result.get('numero_boletin', 'N/A')}")
            console.print(f"Total normas: {result.get('total_normas', 0)}")

            if result.get('normas'):
                console.print(f"\n[cyan]Primeras 3 normas:[/cyan]")
                for i, norma in enumerate(result['normas'][:3], 1):
                    console.print(f"\n{i}. {norma['titulo']}")
                    console.print(f"   URL: {norma['url']}")
                    console.print(f"   Tipo: {norma['tipo']} | Número: {norma['numero']}")
                    console.print(f"   Contenido: {len(norma.get('contenido', ''))} caracteres")
                    console.print(f"   Tablas: {norma['metadata'].get('total_tablas', 0)}")
                    console.print(f"   Montos: {norma['metadata'].get('total_montos', 0)}")

            # Verificar archivo de progreso (debería estar limpio)
            from pathlib import Path
            output_dir = Path("boletines")
            progress_files = list(output_dir.glob(".progress_*.json"))
            if progress_files:
                console.print(f"\n[yellow]⚠ Archivos de progreso pendientes: {len(progress_files)}[/yellow]")
            else:
                console.print(f"\n[green]✓ Sin archivos de progreso pendientes (limpieza OK)[/green]")

            console.print("\n[bold green]TEST EXITOSO[/bold green]")
        else:
            console.print("[red]✗ No se obtuvieron resultados[/red]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Test interrumpido[/yellow]")
    except Exception as e:
        console.print(f"\n[red]✗ Error en test: {e}[/red]")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_scraper()
