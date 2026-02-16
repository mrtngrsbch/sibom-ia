"""
Test directo del RAG query sin levantar servidor
"""
import re
from pathlib import Path
import json
import sys
sys.path.insert(
    0, '/Users/mrtn/Documents/GitHub/sibom-scraper-assistant/chatbot/src')

# Importar el retriever (es TypeScript/JavaScript, necesitamos probar diferente)
# En su lugar, probaremos directamente leyendo los archivos


# Buscar el archivo 2024-T1
file_path = Path('/Users/mrtn/Documents/GitHub/sibom-scraper-assistant/python-cli/boletines/Carlos_Tejedor/Carlos_Tejedor_Balances_20260131_072415_d583d6307bbe.json')

with open(file_path, 'r') as f:
    doc_data = json.load(f)

print(f"🔍 Buscando: Saldo inicial Carlos Tejedor 2024-T1")
print()

# Buscar chunks TIER-1
tier1_chunks = [c for c in doc_data.get(
    'rag_chunks', []) if c.get('tier') == 1]

print(f"✨ Chunks TIER-1 encontrados: {len(tier1_chunks)}")
for chunk in tier1_chunks:
    print(f"\n  📌 {chunk.get('chunk_id', 'unknown')}")
    print(f"     Embedding text: {chunk.get('embedding_text', '')[:150]}...")

    # Extraer saldo_inicial
    data = chunk.get('data', {})
    saldo_inicial = data.get('saldo_inicial', 'N/A')

    print(f"     Saldo Inicial: ${saldo_inicial:,.2f}" if isinstance(
        saldo_inicial, (int, float)) else f"     Saldo Inicial: {saldo_inicial}")

    # Verificar que tiene el valor esperado
    if isinstance(saldo_inicial, (int, float)) and saldo_inicial > 1000000000:
        print(f"     ✅ VALOR CORRECTO ENCONTRADO (> $1B)")
    else:
        print(f"     ❌ Valor no parece correcto")

print("\n" + "="*60)

# Buscar cualquier mención de "469.581" (el total disponibilidades)
print("\n🔎 Buscando 'Total Disponibilidades' ($469.581.055,31) en chunks:")
encontrado = False
for idx, chunk in enumerate(doc_data.get('rag_chunks', [])):
    text = chunk.get('embedding_text', '') + ' ' + \
        json.dumps(chunk.get('data', {}))
    if '469' in text or '469581' in text:
        print(
            f"  ✅ Encontrado en chunk [{chunk.get('tier')}]: {chunk.get('chunk_id')}")
        encontrado = True

if not encontrado:
    print(f"  ❌ No encontrado en ningún chunk")
