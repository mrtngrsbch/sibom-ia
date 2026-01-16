#!/usr/bin/env python3
"""
Obtiene los nombres de ciudades de SIBOM y genera el CITY_MAP.
"""

import requests
import re
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def get_city_name(city_id: int) -> str:
    """Obtiene el nombre de una ciudad desde SIBOM."""
    url = f"https://sibom.slyt.gba.gob.ar/cities/{city_id}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            html = response.text

            # Buscar el título de la página
            match = re.search(r'<title>([^<]+)</title>', html)
            if match:
                title = match.group(1)

                # Extraer nombre del título
                # Formato: "Boletín Oficial Municipal de [Ciudad] - SIBOM"
                match2 = re.search(r'(?:Boletín Oficial Municipal|Municipalidad|Boletín Oficial)\s+(?:de\s+)?([A-ZÁÉÍÓÚÑ][A-Za-záéíóúñÑ\s]+?)(?:\s*[-–—]|SIBOM|$)', title, re.IGNORECASE)
                if match2:
                    name = match2.group(1).strip()
                    # Limpiar trailing characters
                    name = re.sub(r'\s*(?:-|–|—|SIBOM).*$', '', name)
                    return name
    except Exception as e:
        pass

    return None

def generate_city_map(city_ids: list):
    """Genera el CITY_MAP para el rango de IDs especificado."""
    city_map = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"Consultando {len(city_ids)} ciudades...", total=len(city_ids))

        for city_id in city_ids:
            name = get_city_name(city_id)
            if name:
                city_map[str(city_id)] = name
                console.print(f"[dim]  {city_id}: {name}[/dim]")
            else:
                console.print(f"[yellow]  {city_id}: No encontrado[/yellow]")
            progress.update(task, advance=1)

    return city_map

def save_city_map_to_file(city_map: dict, filename: str):
    """Guarda el CITY_MAP en un archivo Python."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# CITY_MAP generado automáticamente desde SIBOM\n")
        f.write("# Generado: {timestamp}\n\n".format(timestamp=__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        f.write("    CITY_MAP = {\n")
        for city_id in sorted(city_map.keys(), key=int):
            f.write(f"        '{city_id}': '{city_map[city_id]}',\n")
        f.write("    }\n")

def main():
    console.print("[bold cyan]Generador de City Map desde SIBOM[/bold cyan]")
    console.print()

    # Rango de IDs a consultar
    start_id = 1
    end_id = 136

    city_ids = list(range(start_id, end_id + 1))
    console.print(f"Consultando ciudades {start_id}-{end_id}...")
    console.print()

    city_map = generate_city_map(city_ids)

    console.print()
    console.print(f"[green]✓ Encontrados {len(city_map)} ciudades[/green]")
    console.print()

    # Mostrar tabla con las primeras 20
    from rich.table import Table
    table = Table(title=f"Ciudades Encontradas (mostrando primeras 20 de {len(city_map)})")
    table.add_column("ID", style="cyan")
    table.add_column("Nombre", style="green")

    for i, city_id in enumerate(sorted(city_map.keys(), key=int)[:20]):
        table.add_row(city_id, city_map[city_id])

    console.print(table)

    # Guardar en archivo
    filename = "boletines/.city_map_sibom.py"
    save_city_map_to_file(city_map, filename)
    console.print()
    console.print(f"[green]✓ CITY_MAP guardado en: {filename}[/green]")
    console.print()
    console.print("[dim]Copia el contenido de CITY_MAP al archivo sibom_scraper.py[/dim]")
    console.print("[dim]Reemplaza la sección CITY_MAP en la clase SIBOMScraper[/dim]")

if __name__ == '__main__':
    main()
