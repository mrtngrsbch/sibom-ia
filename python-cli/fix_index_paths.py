#!/usr/bin/env python3
"""
Fix: Actualizar sb en normativas_index_minimal.json para archivos Balance
"""
import json
from pathlib import Path

index_path = Path('data/indexes/normativas_index_minimal.json')

# Cargar índice
with open(index_path, 'r') as f:
    index = json.load(f)

# Contador de cambios
fixed = 0

# Arreglar entries de balances que tengan sb incorrecto
for entry in index:
    # Si es un balance (t == "balances")
    if entry.get('t') == 'balances':
        sb = entry.get('sb', '')

        # Si sb NOT contiene "/" (no está en formato Municipio/Archivo)
        if sb and '/' not in sb:
            # Extraer el municipio del campo 'm'
            municipality = entry.get('m', '')
            if municipality:
                # Arreglar: sb -> Municipio/sb
                new_sb = f"{municipality.replace(' ', '_')}/{sb}"
                entry['sb'] = new_sb
                fixed += 1
                if fixed <= 5:  # Mostrar primeros 5
                    print(f"  Arreglado: {sb} → {new_sb}")

print(f"\n✅ Total arreglados: {fixed}")

# Guardar índice arreglado
with open(index_path, 'w') as f:
    json.dump(index, f, ensure_ascii=False, indent=1)

print(f"✅ Índice guardado: {index_path}")

# Verificar
with open(index_path, 'r') as f:
    updated = json.load(f)

correct_count = sum(1 for e in updated if e.get(
    't') == 'balances' and '/' in e.get('sb', ''))
print(f"✅ Entries de Balance con sb correcto: {correct_count}")
