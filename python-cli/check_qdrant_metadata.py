#!/usr/bin/env python3
"""Verificar metadata en Qdrant"""

from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()

client = QdrantClient(url=os.getenv('QDRANT_URL'),
                      api_key=os.getenv('QDRANT_API_KEY'))

# Buscar UN punto con source=balance_migration_v1
results = client.scroll(
    collection_name='normativas',
    scroll_filter={
        'must': [{'key': 'source', 'match': {'value': 'balance_migration_v1'}}]},
    limit=1,
    with_payload=True
)

if results and results[0]:
    point = results[0][0]
    print('✅ Punto encontrado con source=balance_migration_v1')
    print(f'ID: {point.id}')
    print(f'Municipio: {point.payload.get("municipio")}')
    print(f'Periodo: {point.payload.get("periodo")}')
    print(
        f'is_executive_summary: {point.payload.get("is_executive_summary")} (type: {type(point.payload.get("is_executive_summary")).__name__})')
    print(
        f'contains_key_numbers: {point.payload.get("contains_key_numbers")} (type: {type(point.payload.get("contains_key_numbers")).__name__})')
    print(f'\nPayload completo:')
    for key, val in point.payload.items():
        print(f'  {key}: {val} ({type(val).__name__})')
else:
    print('❌ NO se encontraron puntos con source=balance_migration_v1')
