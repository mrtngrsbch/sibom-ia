#!/usr/bin/env python3
"""
update_index_with_doctypes.py

Actualiza boletines_index.json con los documentTypes correctos
leídos de cada archivo JSON individual.
"""

import json
from pathlib import Path


def main():
    # Leer índice actual
    with open('boletines_index.json', 'r', encoding='utf-8') as f:
        index = json.load(f)

    # Crear mapa de filename -> documentTypes
    doc_types_map = {}

    print("📁 Leyendo documentTypes de los archivos individuales...")
    for entry in index:
        filename = entry.get('filename', '')
        if not filename:
            continue

        json_path = Path('boletines') / filename
        if json_path.exists():
            try:
                with json_path.open('r', encoding='utf-8') as f:
                    data = json.load(f)
                    doc_types = data.get('documentTypes', [])
                    doc_types_map[filename] = doc_types
            except Exception as e:
                print(f"  ✗ Error leyendo {filename}: {e}")

    # Actualizar índice
    updated = 0
    for entry in index:
        filename = entry.get('filename', '')
        if filename in doc_types_map:
            old_types = entry.get('documentTypes', [])
            new_types = doc_types_map[filename]
            if old_types != new_types:
                entry['documentTypes'] = new_types
                updated += 1

    # Guardar índice actualizado
    with open('boletines_index.json', 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Índice actualizado:")
    print(f"   Entradas actualizadas: {updated}")
    print(f"   Total entradas: {len(index)}")

    # Verificar Carlos Tejedor 2025
    print("\n🔍 Verificando Carlos Tejedor 2025 con decretos:")
    ct_2025_decretos = [
        e for e in index
        if 'carlos' in e.get('municipality', '').lower()
        and '2025' in e.get('date', '')
        and any(t.lower() == 'decreto' for t in e.get('documentTypes', []))
    ]
    for e in ct_2025_decretos[:10]:
        print(f"   {e['date']} - {e['filename']} - {e['documentTypes']}")


if __name__ == '__main__':
    main()
