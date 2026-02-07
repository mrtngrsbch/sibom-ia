#!/usr/bin/env python3
"""
JSON to CSV Converter - SIBOM Boletines
Convierte archivos JSON de boletines a formato CSV

Uso:
  python3 json2csv.py Carlos_Tejedor_81.json     → Carlos_Tejedor_81.csv
  python3 json2csv.py *.json                     → boletines_YY-MM-DD_HH-MM-SS.csv
"""

import json
import csv
import sys
import glob
from datetime import datetime
from pathlib import Path


def json_to_csv_single(json_file: str) -> str:
    """
    Convierte un archivo JSON individual a CSV.

    Args:
        json_file: Ruta al archivo JSON

    Returns:
        Nombre del archivo CSV generado (ruta completa)
    """
    # Leer el JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Generar nombre del CSV en el directorio actual de ejecución
    csv_filename = Path(json_file).stem + '.csv'
    csv_file = Path.cwd() / csv_filename

    # Escribir CSV
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)

        # Escribir encabezados
        headers = ['number', 'date', 'description', 'link', 'status', 'fullText']
        writer.writerow(headers)

        # Escribir datos
        row = [
            data.get('number', ''),
            data.get('date', ''),
            data.get('description', ''),
            data.get('link', ''),
            data.get('status', ''),
            data.get('fullText', '')
        ]
        writer.writerow(row)

    return str(csv_file)


def json_to_csv_multiple(json_files: list) -> str:
    """
    Convierte múltiples archivos JSON a un único CSV consolidado.

    Args:
        json_files: Lista de rutas a archivos JSON

    Returns:
        Nombre del archivo CSV generado (ruta completa)
    """
    # Generar nombre del CSV con timestamp en el directorio actual de ejecución
    timestamp = datetime.now().strftime('%y-%m-%d_%H-%M-%S')
    csv_filename = f'boletines_{timestamp}.csv'
    csv_file = Path.cwd() / csv_filename

    # Leer todos los JSON
    all_data = []
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_data.append(data)
        except Exception as e:
            print(f"⚠ Error leyendo {json_file}: {e}")
            continue

    if not all_data:
        print("❌ No se pudo leer ningún archivo JSON")
        sys.exit(1)

    # Escribir CSV consolidado
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)

        # Escribir encabezados
        headers = ['number', 'date', 'description', 'link', 'status', 'fullText']
        writer.writerow(headers)

        # Escribir cada boletín
        for data in all_data:
            row = [
                data.get('number', ''),
                data.get('date', ''),
                data.get('description', ''),
                data.get('link', ''),
                data.get('status', ''),
                data.get('fullText', '')
            ]
            writer.writerow(row)

    return str(csv_file)


def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python3 json2csv.py Carlos_Tejedor_81.json     → Carlos_Tejedor_81.csv")
        print("  python3 json2csv.py *.json                     → boletines_YY-MM-DD_HH-MM-SS.csv")
        sys.exit(1)

    # Si hay múltiples argumentos, el shell expandió el wildcard (*.json)
    if len(sys.argv) > 2:
        # Múltiples archivos (el shell ya expandió *.json a una lista)
        json_files = sys.argv[1:]  # Todos los argumentos después del nombre del script

        print(f"📂 Encontrados {len(json_files)} archivos JSON")
        csv_file = json_to_csv_multiple(json_files)
        print(f"✅ CSV consolidado generado: {csv_file}")
        print(f"   Total de boletines: {len(json_files)}")

    else:
        # Un solo argumento: puede ser un archivo específico o un patrón con wildcard
        input_pattern = sys.argv[1]

        # Si contiene wildcard, usar glob para expandirlo
        if '*' in input_pattern:
            json_files = glob.glob(input_pattern)

            if not json_files:
                print(f"❌ No se encontraron archivos que coincidan con: {input_pattern}")
                sys.exit(1)

            print(f"📂 Encontrados {len(json_files)} archivos JSON")
            csv_file = json_to_csv_multiple(json_files)
            print(f"✅ CSV consolidado generado: {csv_file}")
            print(f"   Total de boletines: {len(json_files)}")

        else:
            # Archivo único
            json_file = input_pattern

            if not Path(json_file).exists():
                print(f"❌ Archivo no encontrado: {json_file}")
                sys.exit(1)

            csv_file = json_to_csv_single(json_file)
            print(f"✅ CSV generado: {csv_file}")

    print(f"\n🎉 Conversión completada exitosamente")


if __name__ == '__main__':
    main()
