#!/usr/bin/env python3
"""
Script para enriquecer el índice con tipos de documentos extraídos del contenido.

Analiza el fullText de cada documento y extrae todos los tipos mencionados
(ordenanzas, decretos, resoluciones, disposiciones, convenios, licitaciones).
"""

import json
import re
from pathlib import Path
from typing import List, Set

def extract_document_types(full_text: str) -> Set[str]:
    """
    Extrae los tipos de documentos mencionados en el texto.

    Returns:
        Set de tipos encontrados: {'ordenanza', 'decreto', 'resolucion', ...}
    """
    types_found = set()

    # Patrones para detectar cada tipo de documento
    patterns = {
        'ordenanza': r'\bOrdenanza\s*N[°º]\s*\d+',
        'decreto': r'\bDecreto\s*N[°º]\s*\d+',
        'resolucion': r'\bResolución\s*N[°º]\s*\d+',
        'disposicion': r'\bDisposición\s*N[°º]\s*\d+',
        'convenio': r'\bConvenio\s*N[°º]\s*\d+',
        'licitacion': r'\bLicitación\s*N[°º]\s*\d+',
    }

    for doc_type, pattern in patterns.items():
        if re.search(pattern, full_text, re.IGNORECASE):
            types_found.add(doc_type)

    return types_found


def main():
    """Enriquece el índice con tipos de documentos extraídos del contenido."""

    # Cargar índice actual
    index_path = Path('boletines_index.json')

    if not index_path.exists():
        print(f"❌ Error: No se encontró {index_path}")
        return

    print("📖 Cargando índice...")
    with open(index_path, 'r', encoding='utf-8') as f:
        index = json.load(f)

    print(f"✅ Índice cargado: {len(index)} documentos")

    # Directorio de boletines
    boletines_dir = Path('boletines')

    if not boletines_dir.exists():
        print(f"❌ Error: No se encontró el directorio {boletines_dir}")
        return

    # Estadísticas
    stats = {
        'total': len(index),
        'processed': 0,
        'enriched': 0,
        'types': {
            'ordenanza': 0,
            'decreto': 0,
            'resolucion': 0,
            'disposicion': 0,
            'convenio': 0,
            'licitacion': 0,
        }
    }

    print("\n🔍 Procesando documentos...")

    for i, doc in enumerate(index):
        stats['processed'] += 1

        # Cargar el JSON del boletín
        json_path = boletines_dir / doc['filename']

        if not json_path.exists():
            continue

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                boletin_data = json.load(f)

            # Extraer tipos del fullText
            full_text = boletin_data.get('fullText', '')

            if full_text:
                types_found = extract_document_types(full_text)

                if types_found:
                    # Agregar campo 'documentTypes' con array de tipos encontrados
                    doc['documentTypes'] = sorted(list(types_found))
                    stats['enriched'] += 1

                    # Actualizar estadísticas
                    for t in types_found:
                        stats['types'][t] += 1
                else:
                    # Si no encontró tipos específicos, usar el tipo base
                    doc['documentTypes'] = [doc['type']] if doc['type'] else []

        except Exception as e:
            print(f"⚠️  Error procesando {doc['filename']}: {e}")
            continue

        # Mostrar progreso cada 500 documentos
        if (i + 1) % 500 == 0:
            print(f"   Procesados: {i + 1}/{len(index)}")

    # Guardar índice enriquecido
    output_path = Path('boletines_index_enriched.json')

    print(f"\n💾 Guardando índice enriquecido en {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    # Mostrar estadísticas
    print("\n📊 Estadísticas:")
    print(f"   Total documentos: {stats['total']}")
    print(f"   Documentos procesados: {stats['processed']}")
    print(f"   Documentos enriquecidos: {stats['enriched']}")
    print(f"\n   Documentos por tipo:")
    for doc_type, count in sorted(stats['types'].items(), key=lambda x: -x[1]):
        percentage = (count / stats['total']) * 100
        print(f"      {doc_type.capitalize()}: {count:,} ({percentage:.1f}%)")

    print(f"\n✅ Índice enriquecido guardado en {output_path}")
    print(f"\n💡 Siguiente paso: Reemplazar boletines_index.json con el nuevo archivo")


if __name__ == '__main__':
    main()
