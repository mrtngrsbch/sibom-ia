#!/usr/bin/env python3
from extractors.balance_extractor import BalanceExtractor
import json
import sys
sys.path.insert(
    0, '/Users/mrtn/Documents/GitHub/sibom-scraper-assistant/python-cli')


# Cargar el archivo real de Balance 2024-T1
with open('boletines/Carlos_Tejedor/Carlos_Tejedor_Balances_20260131_053424_561e8ab9cebb.json', 'r', encoding='utf-8') as f:
    doc = json.load(f)

print("📄 Documento cargado:")
print(f"   Municipio: {doc['municipio']}")
print(f"   Periodo: {doc['periodo']}")
print(f"   Tipo: {doc['tipo_detalle']}")
print(f"   Contenido longitud: {len(doc['contenido'])} chars\n")

# Testear extractor
extractor = BalanceExtractor(verbose=True)
print("🧪 Extrayendo datos...\n")
summary = extractor.extract(doc)

print(f"\n✅ RESULTADO:")
print(
    f"   Saldo Inicial:        ${summary.saldo_inicial:,.2f}" if summary.saldo_inicial else "   Saldo Inicial: NO encontrado")
print(
    f"   Total Ingresos:       ${summary.total_ingresos_presupuestarios:,.2f}" if summary.total_ingresos_presupuestarios else "   Total Ingresos: NO encontrado")
print(
    f"   Total Egresos:        ${summary.total_egresos:,.2f}" if summary.total_egresos else "   Total Egresos: NO encontrado")
print(
    f"   Saldo Final:          ${summary.saldo_final:,.2f}" if summary.saldo_final else "   Saldo Final: NO encontrado")
print(f"   Completitud:          {summary.completeness_score:.0%}")
print(f"   Campos extraídos:     {summary.campos_extraidos}/7")
print(f"\n   JSON resumen:\n{summary.to_json_str()}")
