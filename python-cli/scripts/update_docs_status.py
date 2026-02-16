#!/usr/bin/env python3
"""
Actualiza automáticamente el archivo docs/Municipios_contenidos.md
basado en los datos realmente descargados en python-cli/boletines/.
"""

import json
import os
from pathlib import Path
from datetime import datetime

# Rutas - Ajustadas asumiendo ejecución desde python-cli/
BASE_DIR = Path(__file__).resolve().parent.parent
BOLETINES_DIR = BASE_DIR / "boletines"
CITY_MAP_FILE = BOLETINES_DIR / "CITY_MAP.json"
DOCS_FILE = BASE_DIR.parent / "docs" / "Municipios_contenidos.md"


def load_city_map():
    if not CITY_MAP_FILE.exists():
        print(f"Error: No se encontró {CITY_MAP_FILE}")
        return {}

    with open(CITY_MAP_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_municipality_data(name):
    # Slugify simple: reemplazar espacios por guiones bajos
    slug = name.replace(" ", "_")
    folder = BOLETINES_DIR / slug

    has_data = False
    file_count = 0

    if folder.exists():
        # Contar archivos JSON que no sean de sistema/progreso
        for f in folder.glob("*.json"):
            if f.name.startswith(".") or f.name.startswith("_"):
                continue
            has_data = True
            file_count += 1

    return has_data, file_count


def generate_markdown(city_map):
    with_data = []
    without_data = []

    total_files = 0

    for city_id, name in sorted(city_map.items(), key=lambda x: x[1]):
        has_data, count = check_municipality_data(name)
        url = f"https://sibom.slyt.gba.gob.ar/cities/{city_id}"

        entry = {
            "name": name,
            "url": url,
            "count": count,
            "id": city_id
        }

        if has_data:
            with_data.append(entry)
            total_files += count
        else:
            without_data.append(entry)

    # Generar contenido del archivo
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    md_content = f"""# Estado de Cobertura de Municipios

> **Última actualización automática:** {timestamp}
> **Total Municipios Soportados:** {len(city_map)}
> **Municipios con Datos:** {len(with_data)}
> **Total Documentos:** {total_files}

Este archivo se genera automáticamente verificando la carpeta `python-cli/boletines/`.

## ✅ Municipios CON Datos ({len(with_data)})

| ID | Municipio | Documentos | Enlace SIBOM |
|:---:|:---|:---:|:---|
"""

    for m in with_data:
        md_content += f"| {m['id']} | **{m['name']}** | {m['count']} | [Ver en SIBOM]({m['url']}) |\n"

    md_content += f"""
## ❌ Municipios SIN Datos Descargados ({len(without_data)})

Puede que estos municipios:
1. No tengan boletines publicados en SIBOM.
2. Aún no se hayan escrapeado (ejecutar `python cli.py sibom --municipality "{without_data[0]['name']}"`).

| ID | Municipio | Enlace SIBOM |
|:---:|:---|:---|
"""

    for m in without_data:
        md_content += f"| {m['id']} | {m['name']} | [Ver en SIBOM]({m['url']}) |\n"

    return md_content


def main():
    print(f"Generando reporte de estado...")
    city_map = load_city_map()
    if not city_map:
        return

    content = generate_markdown(city_map)

    # Asegurar que el directorio docs existe
    DOCS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(DOCS_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Archivo generado exitosamente en: {DOCS_FILE}")


if __name__ == "__main__":
    main()
