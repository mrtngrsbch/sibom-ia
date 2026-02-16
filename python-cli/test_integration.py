#!/usr/bin/env python3
"""
Test de integración del BalanceExtractor con archivos existentes.
"""
import json
from pathlib import Path
from extractors.balance_extractor import BalanceExtractor


def test_existing_file():
    """Prueba con archivo Balance existente (pre-integración)"""
    filepath = Path(
        'boletines/Carlos_Tejedor/Carlos_Tejedor_Balances_20260131_053424_561e8ab9cebb.json')

    with open(filepath, 'r', encoding='utf-8') as f:
        doc = json.load(f)

    # Verificar estado actual
    has_resumen = 'resumen_ejecutivo_numerico' in doc
    print(f"Archivo: {filepath.name}")
    print(
        f"¿Tiene resumen_ejecutivo_numerico? {'SÍ ❌' if has_resumen else 'NO ✅ (esperado)'}")

    if has_resumen:
        print(f"Contenido existente: {doc['resumen_ejecutivo_numerico']}")
        return

    # Extraer resumen
    extractor = BalanceExtractor(verbose=False)
    summary = extractor.extract(doc)

    # Resultados
    print(f"\n🔍 Resultado de extracción:")
    print(
        f"  Saldo Inicial: ${summary.saldo_inicial:,.2f}" if summary.saldo_inicial else "  Saldo Inicial: NO")
    print(
        f"  Total Ingresos: ${summary.total_ingresos_presupuestarios:,.2f}" if summary.total_ingresos_presupuestarios else "  Total Ingresos: NO")
    print(
        f"  Total Egresos: ${summary.total_egresos:,.2f}" if summary.total_egresos else "  Total Egresos: NO")
    print(
        f"  Saldo Final: ${summary.saldo_final:,.2f}" if summary.saldo_final else "  Saldo Final: NO")
    print(f"  Completo: {'✅ SÍ' if summary.is_complete else '❌ NO'}")
    print(f"  Campos extraídos: {summary.campos_extraidos}/7")
    print(f"  Completitud: {int(summary.completeness_score * 100)}%")

    # Mostrar lo que se agregaría al JSON
    if summary.is_complete or summary.campos_extraidos > 0:
        print(f"\n📦 JSON a agregar:")
        print(json.dumps(summary.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    test_existing_file()
