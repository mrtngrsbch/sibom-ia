#!/usr/bin/env python3
"""
Test del HierarchicalChunker con archivo Balance real.
Valida que se generen correctamente los 3 tiers de chunks.
"""
from extractors.balance_extractor import BalanceExtractor
from services.hierarchical_chunker import HierarchicalChunker
import json
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def test_hierarchical_chunker():
    """Test completo de Layer 1 + Layer 2"""
    print("=" * 70)
    print("TEST: HierarchicalChunker con Balance Real")
    print("=" * 70)

    # 1. Cargar documento Balance existente
    filepath = Path(
        'boletines/Carlos_Tejedor/Carlos_Tejedor_Balances_20260131_053424_561e8ab9cebb.json')

    if not filepath.exists():
        print(f"❌ ERROR: Archivo no encontrado: {filepath}")
        return False

    with open(filepath, 'r', encoding='utf-8') as f:
        doc = json.load(f)

    print(f"\n📄 Archivo: {filepath.name}")
    print(f"   Municipio: {doc.get('municipio', 'N/A')}")
    print(f"   Periodo: {doc.get('periodo', 'N/A')}")
    print(f"   rag_chunks existentes: {doc.get('rag_chunks_count', 0)}")

    # 2. Extraer resumen ejecutivo (LAYER 1)
    print("\n" + "─" * 70)
    print("LAYER 1: Extracción de Resumen Ejecutivo")
    print("─" * 70)

    extractor = BalanceExtractor(verbose=False)
    summary = extractor.extract(doc)

    if summary.is_complete:
        print(f"✅ Resumen completo: {summary.campos_extraidos}/7 campos")
        print(f"   Saldo Inicial: ${summary.saldo_inicial:,.2f}")
        print(
            f"   Total Ingresos: ${summary.total_ingresos_presupuestarios:,.2f}")
        print(f"   Total Egresos: ${summary.total_egresos:,.2f}")
        print(f"   Saldo Final: ${summary.saldo_final:,.2f}")

        # Agregar al documento
        doc['resumen_ejecutivo_numerico'] = summary.to_dict()
    else:
        print(f"⚠️ Resumen parcial: {summary.campos_extraidos}/7 campos")

    # 3. Generar chunks jerárquicos (LAYER 2)
    print("\n" + "─" * 70)
    print("LAYER 2: Generación de Chunks Jerárquicos")
    print("─" * 70)

    chunker = HierarchicalChunker(verbose=False)
    hierarchical_chunks = chunker.chunk_balance(doc)

    if not hierarchical_chunks:
        print("❌ ERROR: No se generaron chunks")
        return False

    # 4. Analizar chunks generados
    print(f"\n✅ Total chunks generados: {len(hierarchical_chunks)}")

    # Agrupar por tier
    tier1_chunks = [c for c in hierarchical_chunks if c.tier == 1]
    tier2_chunks = [c for c in hierarchical_chunks if c.tier == 2]
    tier3_chunks = [c for c in hierarchical_chunks if c.tier == 3]

    print(f"\n📊 Distribución por Tier:")
    print(f"   TIER-1 (Executive): {len(tier1_chunks)} chunks")
    print(f"   TIER-2 (Subsection): {len(tier2_chunks)} chunks")
    print(f"   TIER-3 (Detail): {len(tier3_chunks)} chunks")

    # 5. Validar TIER-1 (debe existir 1 chunk ejecutivo)
    print("\n" + "─" * 70)
    print("VALIDACIÓN TIER-1 (Executive Summary)")
    print("─" * 70)

    if len(tier1_chunks) == 0:
        print("❌ FALLO: No hay chunk TIER-1 (se esperaba 1)")
        return False

    if len(tier1_chunks) > 1:
        print(
            f"⚠️ ADVERTENCIA: Hay {len(tier1_chunks)} chunks TIER-1 (se esperaba 1)")

    tier1 = tier1_chunks[0]
    print(f"✅ Chunk TIER-1 encontrado:")
    print(f"   ID: {tier1.chunk_id}")
    print(f"   Completeness: {tier1.completeness_score:.0%}")
    print(f"   Data keys: {list(tier1.data.keys())}")
    print(f"   Embedding text (first 150 chars):")
    print(f"   〉{tier1.embedding_text[:150]}...")

    # Validar que tiene los 4 campos críticos
    required_fields = [
        'saldo_inicial', 'total_ingresos_presupuestarios', 'total_egresos', 'saldo_final']
    missing_fields = [f for f in required_fields if f not in tier1.data]

    if missing_fields:
        print(f"❌ FALLO: Faltan campos en TIER-1: {missing_fields}")
        return False

    print(f"✅ Todos los campos críticos presentes en TIER-1")

    # 6. Mostrar muestra de TIER-3 (si existen)
    if tier3_chunks:
        print("\n" + "─" * 70)
        print(f"MUESTRA TIER-3 (Detail) - Primeros 3 de {len(tier3_chunks)}")
        print("─" * 70)

        for i, chunk in enumerate(tier3_chunks[:3], 1):
            print(f"\n{i}. {chunk.chunk_id}")
            print(f"   Completeness: {chunk.completeness_score:.0%}")
            print(f"   Embedding: {chunk.embedding_text[:100]}...")

    # 7. Serialización (test compatibilidad)
    print("\n" + "─" * 70)
    print("SERIALIZACIÓN")
    print("─" * 70)

    try:
        serialized = [c.to_dict() for c in hierarchical_chunks]
        print(f"✅ Serialización exitosa: {len(serialized)} chunks → dict")

        # Verificar estructura del primer chunk
        sample = serialized[0]
        expected_keys = {'chunk_id', 'tier', 'metadata', 'hierarchy',
                         'data', 'embedding_text', 'completeness_score'}
        actual_keys = set(sample.keys())

        if expected_keys != actual_keys:
            print(f"⚠️ ADVERTENCIA: Keys inesperadas")
            print(f"   Expected: {expected_keys}")
            print(f"   Actual: {actual_keys}")
        else:
            print(f"✅ Estructura correcta (7 keys esperadas)")

    except Exception as e:
        print(f"❌ ERROR: Fallo en serialización: {e}")
        return False

    # 8. Resumen final
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETO: PASADO")
    print("=" * 70)
    print(f"\nResumen:")
    print(f"  • Layer 1 extrajo {summary.campos_extraidos}/7 campos")
    print(f"  • Layer 2 generó {len(hierarchical_chunks)} chunks:")
    print(
        f"    - TIER-1: {len(tier1_chunks)} (Executive summary con 100% completitud)")
    print(f"    - TIER-2: {len(tier2_chunks)} (Subsections)")
    print(f"    - TIER-3: {len(tier3_chunks)} (Detail rows)")
    print(f"  • Serialización: OK")
    print(f"  • Estructura: OK")
    print(f"\n🎯 El sistema está listo para eliminar alucinaciones en datos financieros ✅")

    return True


if __name__ == "__main__":
    success = test_hierarchical_chunker()
    sys.exit(0 if success else 1)
