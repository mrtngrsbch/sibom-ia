#!/usr/bin/env python3
"""
reprocesar_montos.py

Script para re-extraer montos de boletines ya scrapeados.
Útil cuando se mejora el extractor o se quiere actualizar el índice
sin tener que volver a scrapear.

Uso:
    python reprocesar_montos.py                    # Procesa todos
    python reprocesar_montos.py --limit 50         # Solo 50 archivos
    python reprocesar_montos.py --filter Nueve     # Solo archivos que coincidan
"""

from pathlib import Path
from monto_extractor import MontoExtractor
import argparse
import json


def main():
    parser = argparse.ArgumentParser(
        description='Reprocesa montos de boletines existentes'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='boletines',
        help='Directorio con JSONs de boletines'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='montos_index.json',
        help='Archivo de salida'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limitar cantidad de archivos a procesar'
    )
    parser.add_argument(
        '--filter',
        type=str,
        default=None,
        help='Filtrar archivos por nombre (ej: "Nueve" para Nueve de Julio)'
    )

    args = parser.parse_args()

    extractor = MontoExtractor()
    boletines_dir = Path(args.input)

    # Obtener archivos
    json_files = list(boletines_dir.glob('*.json'))

    # Aplicar filtro si existe
    if args.filter:
        json_files = [f for f in json_files if args.filter.lower() in f.name.lower()]

    # Aplicar límite si existe
    if args.limit:
        json_files = json_files[:args.limit]

    print(f"📁 Procesando {len(json_files)} archivos...")

    all_records = []

    for i, json_file in enumerate(json_files, 1):
        try:
            with json_file.open('r', encoding='utf-8') as f:
                boletin = json.load(f)

            records = extractor.extract_from_boletin(boletin)
            if records:
                all_records.extend([r.to_dict() for r in records])
                print(f"[{i}/{len(json_files)}] ✓ {json_file.name}: {len(records)} montos")
            else:
                print(f"[{i}/{len(json_files)}] - {json_file.name}: sin montos")

        except Exception as e:
            print(f"[{i}/{len(json_files)}] ✗ {json_file.name}: error - {e}")

    # Guardar índice
    if all_records:
        extractor._save_index(all_records, Path(args.output))
        print(f"\n💾 Índice guardado: {args.output}")

    extractor._print_stats()


if __name__ == '__main__':
    main()
