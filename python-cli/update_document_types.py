#!/usr/bin/env python3
"""
update_document_types.py

Actualiza el campo documentTypes de boletines ya scrapeados.
Necesario para que funcionen correctamente los filtros por tipo de documento.

Uso:
    python update_document_types.py              # Actualiza todos
    python update_document_types.py --limit 50   # Solo 50 archivos
"""

from pathlib import Path
import re
import json
import argparse


def detect_document_types(text: str) -> list:
    """Detecta tipos de documentos en el texto"""
    if not text:
        return []

    types_found = []
    patterns = {
        'ordenanza': r'\bORDENANZA\s+N[º°]\s*\d+',
        'decreto': r'\bDECRETO\s+N[º°]\s*\d+',
        'resolucion': r'\bRESOLUCI[ÓO]N\s+N[º°]\s*\d+',
        'disposicion': r'\bDISPOSICI[ÓO]N\s+N[º°]\s*\d+',
        'convenio': r'\bCONVENIO\s+(?:INTERINSTITUCIONAL|DE\s+(?:ADHESI[ÓO]N|COLABORACI[ÓO]N))',
        'licitacion': r'\bLICITACI[ÓO]N\s+(?:P[ÚU]BLICA|PRIVADA)',
        'edicto': r'\bEDITO\s+N[º°]\s*\d+',
    }

    text_upper = text.upper()
    for doc_type, pattern in patterns.items():
        if re.search(pattern, text_upper):
            if doc_type not in types_found:
                types_found.append(doc_type)

    return types_found


def update_boletin(filepath: Path) -> dict:
    """Actualiza un solo archivo de boletín"""
    with filepath.open('r', encoding='utf-8') as f:
        data = json.load(f)

    # Usar text_content o fullText
    text = data.get('text_content') or data.get('fullText') or ''

    # Detectar tipos
    document_types = detect_document_types(text)

    # Actualizar si cambió
    old_types = data.get('documentTypes', [])
    if old_types != document_types:
        data['documentTypes'] = document_types

        with filepath.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return {
            'file': filepath.name,
            'old': old_types,
            'new': document_types,
            'updated': True
        }

    return {
        'file': filepath.name,
        'old': old_types,
        'new': document_types,
        'updated': False
    }


def main():
    parser = argparse.ArgumentParser(description='Actualiza documentTypes en boletines existentes')
    parser.add_argument('--input', default='boletines', help='Directorio con JSONs')
    parser.add_argument('--limit', type=int, default=None, help='Limitar cantidad de archivos')

    args = parser.parse_args()

    boletines_dir = Path(args.input)
    json_files = list(boletines_dir.glob('*.json'))

    if args.limit:
        json_files = json_files[:args.limit]

    print(f"📁 Procesando {len(json_files)} archivos...")

    # Contadores
    updated = 0
    with_decreto = 0
    with_ordenanza = 0
    total_decretos = 0
    total_ordenanzas = 0

    for i, json_file in enumerate(json_files, 1):
        result = update_boletin(json_file)

        if result['updated']:
            updated += 1
            print(f"[{i}/{len(json_files)}] ✓ {result['file']}: {result['old']} → {result['new']}")
        else:
            tipos = result['new']
            if 'decreto' in tipos:
                with_decreto += 1
                total_decretos += 1
            if 'ordenanza' in tipos:
                with_ordenanza += 1
                total_ordenanzas += 1
            if i % 100 == 0:
                print(f"[{i}/{len(json_files)}] Procesando...")

    print(f"\n📊 Resumen:")
    print(f"  Archivos actualizados: {updated}")
    print(f"  Con decretos: {with_decreto}")
    print(f"  Con ordenanzas: {with_ordenanza}")


if __name__ == '__main__':
    main()
