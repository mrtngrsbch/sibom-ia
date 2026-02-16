#!/usr/bin/env python3
"""Verificar estado de migración."""

import json
from pathlib import Path
from qdrant_client import QdrantClient
from dotenv import load_dotenv
import os

load_dotenv()

print("\n" + "="*60)
print("📊 ESTADO DE MIGRACIÓN")
print("="*60 + "\n")

# 1. Checkpoint
try:
    with open('data/migration_checkpoint.json') as f:
        checkpoint = json.load(f)

    processed = checkpoint.get('processed_file_paths', [])

    print(f"✅ Checkpoint encontrado:")
    print(f"   Archivos procesados: {len(processed)}")
    print(f"   Última actualización: {checkpoint.get('last_updated', 'N/A')}")
except FileNotFoundError:
    print("⚠️  No se encontró checkpoint")
    processed = []

# 2. Balances disponibles
balance_files = list(Path('boletines').rglob('*Balances*.json'))
balance_tesoreria = []

for bf in balance_files:
    try:
        with open(bf) as f:
            data = json.load(f)
        if data.get('tipo_detalle', '').strip() == 'BALANCE DE TESORERIA':
            balance_tesoreria.append(str(bf))
    except:
        pass

print(f"\n📁 Archivos disponibles:")
print(f"   Total Balances de Tesorería: {len(balance_tesoreria)}")
print(f"   Migrados: {len(processed)}/{len(balance_tesoreria)}")

pendientes = len(balance_tesoreria) - len(processed)
if pendientes > 0:
    print(f"   ⚠️  Pendientes: {pendientes}")
else:
    print(f"   ✅ Todos migrados")

# 3. Qdrant Cloud
try:
    qdrant = QdrantClient(
        url=os.getenv('QDRANT_URL'),
        api_key=os.getenv('QDRANT_API_KEY')
    )

    info = qdrant.get_collection('normativas')

    print(f"\n☁️  Qdrant Cloud:")
    print(f"   Total points: {info.points_count:,}")
    print(f"   Estado: {info.status}")

    # Contar chunks de balances
    balance_points = []
    offset = None

    while True:
        results, offset = qdrant.scroll(
            collection_name='normativas',
            scroll_filter={
                'must': [
                    {'key': 'source', 'match': {'value': 'balance_migration_v1'}}
                ]
            },
            limit=100,
            offset=offset,
            with_payload=False,
            with_vectors=False
        )
        balance_points.extend(results)
        if offset is None:
            break

    print(f"   Points de balances migrados: {len(balance_points)}")

    # Calcular chunks promedio
    if len(processed) > 0:
        avg_chunks = len(balance_points) / len(processed)
        print(f"   Promedio: ~{avg_chunks:.1f} chunks/archivo")

except Exception as e:
    print(f"\n❌ Error conectando a Qdrant: {e}")

print(f"\n" + "="*60)

if pendientes == 0:
    print("✅ MIGRACIÓN COMPLETA - Listo para post-validación")
else:
    print(f"⚠️  MIGRACIÓN EN PROGRESO - {pendientes} archivos restantes")

print("="*60 + "\n")
