#!/usr/bin/env python3
"""
Descubre PDFs de transparencia de Carlos Tejedor
y actualiza sources_user.yaml automáticamente.

Este script scrapea las páginas de transparencia del municipio,
extrae los enlaces a los archivos PDF y genera un archivo YAML
actualizado con todas las URLs descubiertas.

Uso:
    cd python-cli
    python scripts/discover_carlos_tejedor.py
    python scripts/discover_carlos_tejedor.py --category balances

@version 1.0.0
@created 2026-01-30
"""

import argparse
import asyncio
import httpx
from bs4 import BeautifulSoup
import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table
from urllib.parse import urljoin

# Importar configuración
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import USER_SOURCES_FILE, SOURCES_FILE

console = Console()

BASE_URL = "https://carlostejedor.gob.ar"

# Configuración de categorías
CATEGORIES = {
    "balances": {
        "url": f"{BASE_URL}/balances/",
        "name": "Carlos Tejedor - Balances",
        "categories": ["balances"],
        "document_types": [
            "balance_sumas_saldos",
            "balance_tesoreria",
            "gastos",
            "gastos_por_finalidad",
            "recursos",
            "situacion_economica",
            "stock_deuda"
        ]
    },
    "presupuestos": {
        "url": f"{BASE_URL}/presupuestos/",
        "name": "Carlos Tejedor - Presupuestos",
        "categories": ["presupuestos"],
        "document_types": [
            "gastos_por_caracter",
            "gastos_por_categoria",
            "gastos_por_finalidad",
            "gastos_por_fuente",
            "gastos_por_objeto",
            "recursos_por_caracter",
            "recursos_por_procedencia",
            "recursos_por_rubro"
        ]
    },
    "concursos": {
        "url": f"{BASE_URL}/concursodeprecios/",
        "name": "Carlos Tejedor - Concursos",
        "categories": ["concursos"],
        "document_types": ["concurso_precios"]
    },
    "licitaciones_privadas": {
        "url": f"{BASE_URL}/licitacionesprivadas/",
        "name": "Carlos Tejedor - Licitaciones Privadas",
        "categories": ["licitaciones"],
        "document_types": ["licitacion_privada"]
    },
    "licitaciones_publicas": {
        "url": f"{BASE_URL}/licitacionespublicas/",
        "name": "Carlos Tejedor - Licitaciones Públicas",
        "categories": ["licitaciones"],
        "document_types": ["licitacion_publica"]
    },
}


async def discover_pdfs_in_page(url: str, category: str) -> list:
    """
    Descubre PDFs en una página de transparencia.

    Args:
        url: URL de la página a scrapear
        category: Nombre de la categoría (para logging)

    Returns:
        Lista de URLs completas de PDFs encontrados
    """
    console.print(f"  [dim]Scrapeando: {url}[/dim]")

    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code != 200:
                console.print(f"  [red]Error HTTP {response.status_code}: {url}[/red]")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            pdfs = []
            seen_names = set()

            # Buscar enlaces a PDFs
            for link in soup.find_all('a', href=True):
                href = link['href']

                # Solo enlaces que contengan simple-file-list y terminen en .pdf
                if '/simple-file-list/' in href and href.endswith('.pdf'):
                    # Convertir URL relativa a absoluta si es necesario
                    full_url = urljoin(BASE_URL, href)

                    # Extraer nombre del archivo
                    filename = full_url.split('/')[-1]

                    # Evitar duplicados por nombre de archivo
                    if filename not in seen_names:
                        seen_names.add(filename)
                        pdfs.append(full_url)

            console.print(f"  [green]✓ {len(pdfs)} PDFs encontrados[/green]")
            return pdfs

    except Exception as e:
        console.print(f"  [red]Error: {e}[/red]")
        return []


async def discover_categories(categories: list[str]) -> list:
    """
    Descubre PDFs para las categorías especificadas.

    Args:
        categories: Lista de categorías a descubrir

    Returns:
        Lista de fuentes YAML con URLs descubiertas
    """
    all_sources = []

    for category_key in categories:
        if category_key not in CATEGORIES:
            console.print(f"[yellow]⚠️ Categoría desconocida: {category_key}[/yellow]")
            continue

        config = CATEGORIES[category_key]
        console.print(f"\n[cyan]🔍 Descubriendo: {config['name']}[/cyan]")

        pdfs = await discover_pdfs_in_page(config['url'], category_key)

        if pdfs:
            source = {
                "name": config["name"],
                "type": "manual",
                "enabled": category_key == "balances",  # Solo balances habilitado por defecto
                "base_url": config["url"],
                "categories": config["categories"],
                "url_patterns": sorted(pdfs),  # URLs ordenadas para consistencia
                "document_types": config["document_types"],
                "description": f"Carlos Tejedor - {category_key.replace('_', ' ').title()}"
            }
            all_sources.append(source)
        else:
            console.print(f"  [yellow]⚠️ No se encontraron PDFs para {category_key}[/yellow]")

    return all_sources


def create_yaml_with_sources(sources: list, output_file: Path) -> None:
    """
    Crea un archivo YAML con las fuentes descubiertas.

    Args:
        sources: Lista de fuentes YAML
        output_file: Ruta del archivo de salida
    """
    # Crear contenido YAML
    yaml_content = {
        "sources": sources
    }

    # Agregar comentario de uso
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open('w', encoding='utf-8') as f:
        f.write("# Fuentes de datos personalizadas - Carlos Tejedor\n")
        f.write("# Generado automáticamente por scripts/discover_carlos_tejedor.py\n")
        f.write(f"# Fecha: {asyncio.get_event_loop().time()}\n")
        f.write("#\n")
        f.write("# Para activar una fuente, cambia enabled: false → enabled: true\n")
        f.write("#\n")

        yaml.dump(yaml_content, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    console.print(f"\n[green]✓ YAML actualizado: {output_file}[/green]")


def print_summary(sources: list) -> None:
    """Imprime un resumen de los PDFs descubiertos"""
    total_pdfs = sum(len(s.get("url_patterns", [])) for s in sources)

    console.print(f"\n[bold cyan]📊 Resumen del descubrimiento:[/bold cyan]")
    console.print(f"  Categorías encontradas: {len(sources)}")
    console.print(f"  Total PDFs: {total_pdfs}")

    # Crear tabla detallada
    table = Table(title="\nPDFs por Categoría")
    table.add_column("Categoría", style="cyan")
    table.add_column("PDFs", style="green", justify="right")
    table.add_column("Estado", style="yellow")

    for source in sources:
        name = source["name"].replace("Carlos Tejedor - ", "")
        count = len(source.get("url_patterns", []))
        status = "✓ Habilitado" if source.get("enabled") else "— Deshabilitado"
        table.add_row(name, str(count), status)

    console.print(table)


async def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Descubre PDFs de transparencia de Carlos Tejedor"
    )
    parser.add_argument(
        "--category",
        choices=list(CATEGORIES.keys()),
        nargs="+",
        help="Categorías a descubrir (default: todas)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=USER_SOURCES_FILE,
        help="Archivo YAML de salida"
    )
    parser.add_argument(
        "--enable-all",
        action="store_true",
        help="Habilitar todas las categorías descubiertas"
    )

    args = parser.parse_args()

    console.print("[bold cyan]Carlos Tejedor Transparency Discovery[/bold cyan]")
    console.print()

    # Determinar categorías a procesar
    if args.category:
        categories_to_process = args.category
        console.print(f"Categorías: {', '.join(categories_to_process)}")
    else:
        categories_to_process = ["balances"]  # Default: solo balances
        console.print(f"Categorías: {', '.join(categories_to_process)} (default)")
        console.print("[dim]Usa --category para descubrir otras categorías[/dim]")

    console.print()

    # Descubrir PDFs
    sources = await discover_categories(categories_to_process)

    if not sources:
        console.print("[yellow]⚠️ No se encontraron fuentes[/yellow]")
        return

    # Habilitar todas si se solicita
    if args.enable_all:
        for source in sources:
            source["enabled"] = True

    # Imprimir resumen
    print_summary(sources)

    # Crear YAML
    create_yaml_with_sources(sources, args.output)

    console.print("\n[dim]Para usar estas fuentes:[/dim]")
    console.print("  python cli.py transparency --municipality \"Carlos Tejedor\" --category balances")


if __name__ == "__main__":
    asyncio.run(main())
