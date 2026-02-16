#!/usr/bin/env python3
"""Verificar por qué faltan resúmenes ejecutivos en 2024-T1"""

import json
from pathlib import Path

# Buscar archivos de balance con fecha 2024
files = list(Path('boletines/Carlos_Tejedor').glob('*Balances*.json'))

print("🔍 Analizando archivos de balances Carlos Tejedor...")
print()

found_2024 = []
for f in files:
    try:
        data = json.loads(f.read_text(encoding='utf-8'))
        fecha = data.get('fecha_documento', '')

        if '2024' in str(fecha) and data.get('tipo_detalle') == 'BALANCE DE TESORERIA':
            found_2024.append((f, data))
    except Exception as e:
        continue

if not found_2024:
    print("❌ NO se encontraron archivos Balance de Tesorería 2024")
    print("\nBuscando cualquier balance 2024...")

    for f in files:
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
            if '2024' in str(data.get('fecha_documento', '')):
                print(f"Encontrado: {f.name}")
                print(f"  Tipo detalle: {data.get('tipo_detalle')}")
        except:
            pass
else:
    print(
        f"✅ Encontrados {len(found_2024)} archivos Balance de Tesorería 2024\n")

    for f, data in found_2024[:3]:
        print(f"📄 {f.name}")
        print(f"   Fecha: {data.get('fecha_documento')}")
        print(f"   Periodo: {data.get('periodo')}")
        print(f"   Tipo detalle: {data.get('tipo_detalle')}")

        # Verificar resumen ejecutivo
        if 'resumen_ejecutivo' in data:
            resumen = data['resumen_ejecutivo']
            print(f"   ✅ Tiene resumen_ejecutivo ({len(resumen)} chars)")

            # Buscar "saldo inicial" en resumen
            if 'saldo inicial' in resumen.lower():
                print(f"   ✅ Contiene 'saldo inicial'")

                # Extraer línea con saldo inicial
                for line in resumen.split('\n'):
                    if 'saldo inicial' in line.lower():
                        print(f"      {line}")
            else:
                print(f"   ⚠️  NO contiene 'saldo inicial'")
        else:
            print(f"   ❌ NO tiene resumen_ejecutivo")

        # Verificar tablas
        if 'tablas' in data:
            print(f"   Tablas: {len(data['tablas'])}")

        print()
