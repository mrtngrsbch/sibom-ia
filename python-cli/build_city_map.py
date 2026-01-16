#!/usr/bin/env python3
"""
Inicializa el mapa de ciudades desde los archivos JSON existentes.
Este script lee todos los archivos JSON en boletines/ y construye un mapeo
de IDs a nombres de ciudades.
"""

import json
import re
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

def extract_city_id_from_url(url: str) -> str:
    """Extrae el ID de la ciudad desde la URL."""
    match = re.search(r'/cities/(\d+)', url)
    if match:
        return match.group(1)
    return None

def build_city_map():
    """Construye el mapa de ciudades desde archivos JSON existentes."""
    boletines_dir = Path("boletines")

    if not boletines_dir.exists():
        console.print("[red]Error: La carpeta boletines/ no existe[/red]")
        return None

    city_map = {}  # city_id -> [nombres encontrados]

    console.print("[cyan]Escaneando archivos JSON en boletines/...[/cyan]")

    json_files = list(boletines_dir.glob("*.json"))
    console.print(f"[dim]Encontrados {len(json_files)} archivos JSON[/dim]")

    for json_file in json_files:
        try:
            with json_file.open('r', encoding='utf-8') as f:
                data = json.load(f)

            # Extraer municipio
            municipio = None
            if 'municipio' in data:
                municipio = data['municipio']

            # Extraer URL del boletín para obtener el ID de la ciudad
            city_id = None
            if 'boletin_url' in data:
                city_id = extract_city_id_from_url(data['boletin_url'])

            if municipio and city_id:
                if city_id not in city_map:
                    city_map[city_id] = set()
                city_map[city_id].add(municipio)

        except Exception as e:
            console.print(f"[yellow]Error leyendo {json_file.name}: {e}[/yellow]")

    # Resumir el mapa (tomar el nombre más común para cada ID)
    final_map = {}
    for city_id, names in city_map.items():
        # Tomar el nombre más largo (usualmente más completo)
        final_map[city_id] = max(names, key=len)

    return final_map

def generate_city_map_code(city_map: dict) -> str:
    """Genera el código Python para el CITY_MAP."""
    lines = ['    CITY_MAP = {']
    for city_id in sorted(city_map.keys(), key=int):
        lines.append(f"        '{city_id}': '{city_map[city_id]}',")
    lines.append('    }')
    return '\n'.join(lines)

def main():
    console.print("[bold cyan]Generador de City Map[/bold cyan]")
    console.print()

    city_map = build_city_map()

    if not city_map:
        console.print("[red]No se pudo construir el mapa de ciudades[/red]")
        return

    console.print(f"[green]✓ Encontrados {len(city_map)} ciudades[/green]")
    console.print()

    # Mostrar tabla
    table = Table(title="Mapeo de Ciudades")
    table.add_column("ID", style="cyan")
    table.add_column("Nombre", style="green")
    table.add_column("Ocurrencias", style="yellow")

    # Contar ocurrencias originales
    for city_id in sorted(city_map.keys(), key=int):
        table.add_row(city_id, city_map[city_id], "1")

    console.print(table)
    console.print()

    # Generar código
    code = generate_city_map_code(city_map)

    console.print("[bold]Código generado para sibom_scraper.py:[/bold]")
    console.print()

    # Guardar en archivo
    output_file = Path("boletines/.city_map_generated.py")
    with output_file.open('w', encoding='utf-8') as f:
        f.write("# CITY_MAP generado desde archivos JSON\n")
        f.write("# Copia este código a la clase SIBOMScraper en sibom_scraper.py\n\n")
        f.write(code)

    console.print(f"[green]✓ Código guardado en: {output_file}[/green]")
    console.print()
    console.print("[dim]Copia el contenido de CITY_MAP al archivo sibom_scraper.py[/dim]")

if __name__ == '__main__':
    main()
