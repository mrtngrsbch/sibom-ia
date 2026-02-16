#!/usr/bin/env python3
"""Verificar si existen balances 2024-T1 en Qdrant"""

from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()

client = QdrantClient(url=os.getenv('QDRANT_URL'),
                      api_key=os.getenv('QDRANT_API_KEY'))

print("🔍 Buscando balances Carlos Tejedor 2024-T1...")
print()

# Buscar chunks con periodo 2024-T1
results = client.scroll(
    collection_name='normativas',
    scroll_filter={'must': [
        {'key': 'source', 'match': {'value': 'balance_migration_v1'}},
        {'key': 'municipio', 'match': {'value': 'Carlos Tejedor'}},
        {'key': 'periodo', 'match': {'value': '2024-T1'}}
    ]},
    limit=10,
    with_payload=True
)

if results and results[0]:
    print(
        f"✅ Encontrados {len(results[0])} chunks para Carlos Tejedor 2024-T1")
    print()

    # Mostrar resúmenes ejecutivos
    executive_summaries = [p for p in results[0]
                           if p.payload.get('is_executive_summary')]
    print(f"Resúmenes ejecutivos: {len(executive_summaries)}")

    if executive_summaries:
        for i, point in enumerate(executive_summaries, 1):
            print(f"\n📊 Resumen {i}:")
            print(f"   ID: {point.id}")
            print(f"   Periodo: {point.payload.get('periodo')}")
            print(f"   Tipo chunk: {point.payload.get('chunk_type')}")
            print(
                f"   Contiene números: {point.payload.get('contains_key_numbers')}")

            # Extraer primeros 300 chars del texto
            text = point.payload.get('chunk_text', '')
            print(f"   Texto (primeros 300 chars):")
            print(f"   {text[:300]}...")

            # Buscar "saldo inicial" en el texto
            if 'saldo inicial' in text.lower():
                lines = text.split('\n')
                for line in lines:
                    if 'saldo inicial' in line.lower():
                        print(f"\n   🔍 LÍNEA CON SALDO INICIAL:")
                        print(f"   {line}")

    # Mostrar tablas
    tables = [p for p in results[0] if p.payload.get('chunk_type') == 'table']
    print(f"\n\nTablas: {len(tables)}")

    if tables:
        print(f"\nPrimera tabla (primeros 500 chars):")
        first_table = tables[0].payload.get('chunk_text', '')
        print(first_table[:500])

        # Buscar saldo inicial en tabla
        if 'saldo inicial' in first_table.lower() or '469.581.055' in first_table:
            print("\n✅ TABLA CONTIENE SALDO INICIAL CORRECTO")
        else:
            print("\n⚠️ Tabla no contiene saldo inicial o es diferente")

else:
    print("❌ NO se encontraron balances para Carlos Tejedor 2024-T1")
    print()
    print("Verificando otros períodos disponibles...")

    # Buscar todos los períodos de Carlos Tejedor
    all_periods = client.scroll(
        collection_name='normativas',
        scroll_filter={'must': [
            {'key': 'source', 'match': {'value': 'balance_migration_v1'}},
            {'key': 'municipio', 'match': {'value': 'Carlos Tejedor'}}
        ]},
        limit=100,
        with_payload=['periodo']
    )

    if all_periods and all_periods[0]:
        periods = set(p.payload.get('periodo')
                      for p in all_periods[0] if p.payload.get('periodo'))
        print(f"\nPeríodos disponibles: {sorted(periods)}")
