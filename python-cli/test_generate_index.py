#!/usr/bin/env python3
"""
Script de prueba: Generar índice minimal desde archivo V2
"""

import json
from pathlib import Path
from datetime import datetime
from normativas_extractor import Normativa, save_minimal_index

# Leer archivo V2
test_file = Path("boletines/Test_Quick.json")
with test_file.open('r', encoding='utf-8') as f:
    data = json.load(f)

# Convertir normas V2 a objetos Normativa
normativas = []
municipio = data.get('municipio', '')
boletin_url = data.get('boletin_url', '')
bulletin_id = 'Test_Quick'

for norma in data.get('normas', []):
    # Extraer año
    year = ''
    if '/' in norma['numero']:
        year = norma['numero'].split('/')[-1]
    elif norma.get('fecha'):
        parts = norma['fecha'].split('/')
        if len(parts) == 3:
            year = parts[2]

    normativa = Normativa(
        id=norma['id'],
        municipality=municipio,
        type=norma['tipo'],
        number=norma['numero'],
        year=year,
        date=norma.get('fecha', ''),
        title=norma['titulo'],
        content=norma.get('contenido', ''),
        source_bulletin=bulletin_id,
        source_bulletin_url=boletin_url,
        norma_url=norma['url'],  # ¡URL individual de V2!
        doc_index=0,
        status='vigente',
        extracted_at=datetime.now().isoformat()
    )
    normativas.append(normativa)

# Guardar índice minimal
output_path = Path("normativas_index_minimal_test.json")
save_minimal_index(normativas, output_path)

print(f"\n✅ Índice minimal de prueba generado: {output_path}")
print(f"   Total normativas: {len(normativas)}")
print(f"\nPrimera norma (verificar URL individual):")
print(f"  URL: {normativas[0].norma_url}")
