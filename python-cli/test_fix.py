"""
Test del fix de hierarchical_chunker
"""
import json
from pathlib import Path
from services.hierarchical_chunker import HierarchicalChunker

# Cargar archivo específico de 2024-T1
test_file = Path(
    'boletines/Carlos_Tejedor/Carlos_Tejedor_Balances_20260131_072415_d583d6307bbe.json')

with open(test_file, 'r') as f:
    doc_data = json.load(f)

# Crear chunker con verbose
chunker = HierarchicalChunker(verbose=True)

# Generar TIER-1 chunk
print("🔍 Extrayendo tabla de totales...")
totales = chunker._extract_critical_totals_from_tables(
    doc_data.get('tablas_md', []))
print(f"\n📊 Totales extraídos de tablas:")
for key, val in totales.items():
    print(f"  {key}: ${val:,.2f}")

print("\n" + "="*60)
print("📥 Generando chunks jerárquicos...")
chunks = chunker.chunk_balance(doc_data)

print(f"\n✅ Generados {len(chunks)} chunks:")
for chunk in chunks:
    print(f"\n  [{chunk.tier}] {chunk.chunk_id}")
    print(f"      Texto: {chunk.embedding_text[:100]}...")
    if chunk.tier == 1:
        print(f"      Datos: {chunk.data}")
