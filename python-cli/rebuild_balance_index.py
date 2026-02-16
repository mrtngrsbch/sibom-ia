#!/usr/bin/env python3
"""Extraer títulos descriptivos desde la BD y actualizar index."""

import sqlite3
import json
from pathlib import Path

print("=" * 70)
print("RECONSTRUIR INDICE CON TÍTULOS CORREGIDOS")
print("=" * 70)

db_path = "data/normativas.db"
balance_dir = Path("boletines/Carlos_Tejedor")
index_output = Path("../data/indexes/normativas_index_minimal.json")
index_output.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Para cada balance en BD, obtener el json_file y extraer título
print("\n📥 Leyendo JSONs de balance...")

balance_json_map = {}  # json_file -> titulo
json_files_found = []

# Mapear archivos físicos disponibles
all_json_files = list(balance_dir.glob("*Balance*.json"))
print(f"Encontrados {len(all_json_files)} archivos Balance JSON")

for json_file in all_json_files:
    try:
        with open(json_file) as f:
            data = json.load(f)

        # Extraer título desde cabecera
        cabecera = data.get('cabecera', {})
        tipo = cabecera.get('tipo_documento', '').strip()

        # Si tipo está vacío, usar default de Carlos Tejedor
        if not tipo:
            tipo = "BALANCE DE SUMAS Y SALDOS"

        tipo = tipo.upper()

        ejercicio = cabecera.get('ejercicio', '').strip()

        # Construir título final: Tipo + Año
        if ejercicio:
            title = f"{tipo} - {ejercicio}"
        else:
            title = tipo

        # Guardar con path completa relativa
        rel_path = f"Carlos_Tejedor/{json_file.name}"
        balance_json_map[rel_path] = title
        json_files_found.append(rel_path)

    except Exception as e:
        print(f"⚠️  Error en {json_file.name}: {e}")

print(f"✅ Mapa de títulos creado: {len(balance_json_map)} archivos")

# 2. Actualizar BD con los títulos
print("\n🔄 Actualizando base de datos...")
updated = 0
for json_file, title in balance_json_map.items():
    cursor.execute(
        "UPDATE transparency_docs SET titulo_extraido = ? WHERE json_file = ? AND tipo_documento LIKE '%balance%'",
        (title, json_file)
    )
    updated += cursor.rowcount

conn.commit()
print(f"✅ Actualizados {updated} registros en BD")

# 3. Ahora reconstruir índice completo desde BD
print("\n📤 Reconstruyendo índice completo...")
cursor.execute("""
    SELECT 
        id,
        municipio as m,
        tipo_documento as t,
        periodo as y,
        fecha_documento as d,
        titulo_extraido as titulo,
        json_file as sb,
        url_origen as url
    FROM transparency_docs
    ORDER BY id DESC
""")

records = []
for row in cursor.fetchall():
    # Extraer año del periodo (ej: "2024-T1" -> 2024, "2024" -> 2024)
    periodo = row[3] or ''
    year = None
    if periodo:
        year_str = periodo.split(
            '-')[0] if isinstance(periodo, str) else str(periodo)
        try:
            year = int(year_str)
        except:
            year = None

    records.append({
        'id': row[0],
        'm': row[1],
        't': row[2],
        'y': year,  # Año como número, no string
        'd': row[4],
        'ti': row[5],
        'sb': row[6],
        'url': row[7]
    })

# Guardar índice
with open(index_output, 'w') as f:
    json.dump(records, f)

print(f"✅ Índice guardado: {index_output}")
print(f"✅ Total de registros: {len(records)}")

# 4. Verificar balances en índice
balances_with_title = sum(1 for r in records if 'balance' in r['t'].lower(
) and r['ti'] and r['ti'] != '**CABECERA DEL DOCUMENTO**')
print(f"✅ Balances con título correcto: {balances_with_title}")

# Ver ejemplos
print("\n📋 Ejemplos de títulos:")
for r in [rec for rec in records if 'balance' in rec['t'].lower()][:5]:
    title = r['ti'] if r['ti'] else "(vacío)"
    print(f"   • {title[:70]}")

conn.close()
print("\n" + "=" * 70)
print("✅ OPERACIÓN COMPLETADA")
print(f"📍 Índice listo en: {index_output}")
print("=" * 70)
