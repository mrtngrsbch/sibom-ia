#!/bin/bash
# Script para actualizar y enriquecer el índice de boletines
# Puede ser ejecutado manualmente o desde el botón "Actualizar datos" del frontend

set -e  # Salir si hay algún error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔄 Actualizando índice de boletines..."
echo ""

# Paso 1: Regenerar índice desde los archivos JSON existentes
echo "📋 Paso 1/2: Regenerando índice desde archivos JSON..."
python3 indexar_boletines.py

if [ $? -ne 0 ]; then
    echo "❌ Error regenerando el índice"
    exit 1
fi

echo "✅ Índice regenerado"
echo ""

# Paso 2: Enriquecer con tipos de documentos
echo "🔍 Paso 2/2: Enriqueciendo índice con tipos de documentos..."
python3 enrich_index_with_types.py

if [ $? -ne 0 ]; then
    echo "❌ Error enriqueciendo el índice"
    exit 1
fi

# Reemplazar índice con el enriquecido
if [ -f "boletines_index_enriched.json" ]; then
    # Backup del índice anterior
    if [ -f "boletines_index.json" ]; then
        cp boletines_index.json boletines_index_backup.json
        echo "💾 Backup creado: boletines_index_backup.json"
    fi

    # Reemplazar
    mv boletines_index_enriched.json boletines_index.json
    echo "✅ Índice actualizado con tipos de documentos"
else
    echo "❌ No se encontró boletines_index_enriched.json"
    exit 1
fi

echo ""
echo "🎉 Proceso completado exitosamente"
echo ""
echo "📊 Estadísticas del índice actualizado:"
python3 -c "
import json
with open('boletines_index.json', 'r') as f:
    index = json.load(f)

total = len(index)
with_types = sum(1 for d in index if 'documentTypes' in d and d['documentTypes'])

print(f'   Total documentos: {total:,}')
print(f'   Con tipos enriquecidos: {with_types:,} ({with_types/total*100:.1f}%)')

# Contar por tipo
types_count = {}
for doc in index:
    if 'documentTypes' in doc:
        for t in doc['documentTypes']:
            types_count[t] = types_count.get(t, 0) + 1

print('')
print('   Documentos por tipo:')
for t, count in sorted(types_count.items(), key=lambda x: -x[1]):
    print(f'      {t.capitalize()}: {count:,}')
"

exit 0
