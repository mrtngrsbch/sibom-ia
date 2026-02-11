#!/usr/bin/env python3
"""
Script de inicialización para generar el mapeo completo de ciudades.
Este script consulta SIBOM para obtener el nombre de todas las ciudades y
genera un archivo CITY_MAP.json con el mapeo completo de IDs a nombres.
"""

import requests
import re
import json
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def get_city_name(city_id: int) -> str:
    """
    Obtiene el nombre de una ciudad desde SIBOM.

    Args:
        city_id: ID de la ciudad

    Returns:
        Nombre de la ciudad o None si no se puede obtener
    """
    url = f"https://sibom.slyt.gba.gob.ar/cities/{city_id}"

    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        if response.status_code == 200:
            html = response.text

            # Buscar en el primer boletín de la página
            # Formato: <p class="bulletin-title">XXº de [Ciudad]</p>
            match = re.search(r'<p[^>]*class="[^"]*bulletin-title[^"]*"[^>]*>([^<]+)</p>', html, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # Formato típico: "105º de Carlos Tejedor"
                name_match = re.search(r'º?\s+de\s+([A-ZÁÉÍÓÚÑ][A-Za-záéíóúñÑ\s]+)', title)
                if name_match:
                    name = name_match.group(1).strip()
                    return name

    except Exception as e:
        pass

    return None

def generate_city_map(start_id: int, end_id: int) -> dict:
    """
    Genera el mapeo de IDs a nombres consultando SIBOM.

    Args:
        start_id: ID de inicio
        end_id: ID de fin

    Returns:
        Dict con el mapeo de IDs a nombres
    """
    city_map = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"Consultando ciudades {start_id}-{end_id}...", total=end_id - start_id + 1)

        for city_id in range(start_id, end_id + 1):
            name = get_city_name(city_id)
            if name:
                city_map[str(city_id)] = name
                console.print(f"[dim]  {city_id}: {name}[/dim]")
            else:
                console.print(f"[yellow]  {city_id}: No encontrado[/yellow]")
            progress.update(task, advance=1)

    return city_map

def save_city_map(city_map: dict, output_file: Path):
    """
    Guarda el mapeo de ciudades en un archivo JSON.

    Args:
        city_map: Dict con el mapeo de IDs a nombres
        output_file: Ruta del archivo de salida
    """
    with output_file.open('w', encoding='utf-8') as f:
        json.dump(city_map, f, indent=2, ensure_ascii=False)

def main():
    console.print("[bold cyan]Inicialización de City Map[/bold cyan]")
    console.print()
    console.print("Este script generará un mapeo completo de IDs a nombres")
    console.print("consultando SIBOM para cada ciudad.")
    console.print()

    # Rango de IDs a consultar
    start_id = 1
    end_id = 136

    console.print(f"Consultando ciudades {start_id}-{end_id}...")
    console.print()

    city_map = generate_city_map(start_id, end_id)

    console.print()
    console.print(f"[green]✓ Encontradas {len(city_map)} ciudades[/green]")
    console.print()

    # Mostrar tabla con las primeras 20 ciudades
    from rich.table import Table
    table = Table(title=f"Ciudades Encontradas (mostrando primeras 20 de {len(city_map)})")
    table.add_column("ID", style="cyan")
    table.add_column("Nombre", style="green")

    for i, city_id in enumerate(sorted(city_map.keys(), key=int)[:20]):
        table.add_row(city_id, city_map[city_id])

    console.print(table)
    console.print()

    # Guardar en archivo
    output_file = Path("boletines/CITY_MAP.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    save_city_map(city_map, output_file)

    console.print(f"[green]✓ CITY_MAP guardado en: {output_file}[/green]")
    console.print()
    console.print("[bold]Siguiente paso:[/bold]")
    console.print("El scraper ahora usará este archivo para mostrar los nombres de ciudades.")
    console.print("No necesitas hacer nada más.")

if __name__ == '__main__':
    main()
