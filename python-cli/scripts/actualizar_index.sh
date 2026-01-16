#!/bin/bash
# Script para actualizar la base de datos SQLite de boletines
# Puede ser ejecutado manualmente o desde el botón "Actualizar datos" del frontend

set -e  # Salir si hay algún error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔄 Actualizando base de datos de boletines..."
echo ""

# Generar base de datos SQLite desde archivos JSON
echo "📋 Generando base de datos SQLite desde archivos JSON..."
python3 build_database.py

if [ $? -ne 0 ]; then
    echo "❌ Error generando la base de datos"
    exit 1
fi

echo "✅ Base de datos generada exitosamente"
echo ""

# Mostrar estadísticas
echo "📊 Estadísticas de la base de datos:"
python3 -c "
import sqlite3
import os

db_path = 'boletines/normativas.db'
if not os.path.exists(db_path):
    print('   ❌ Base de datos no encontrada')
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Total de normativas
cursor.execute('SELECT COUNT(*) FROM normativas')
total = cursor.fetchone()[0]
print(f'   Total normativas: {total:,}')

# Por municipio
cursor.execute('''
    SELECT municipality, COUNT(*) as count 
    FROM normativas 
    GROUP BY municipality 
    ORDER BY count DESC
''')
print('')
print('   Por municipio:')
for row in cursor.fetchall():
    print(f'      {row[0]}: {row[1]:,}')

# Por tipo
cursor.execute('''
    SELECT type, COUNT(*) as count 
    FROM normativas 
    GROUP BY type 
    ORDER BY count DESC
''')
print('')
print('   Por tipo:')
for row in cursor.fetchall():
    print(f'      {row[0].capitalize()}: {row[1]:,}')

# Por año
cursor.execute('''
    SELECT strftime('%Y', date) as year, COUNT(*) as count 
    FROM normativas 
    WHERE date IS NOT NULL
    GROUP BY year 
    ORDER BY year DESC
    LIMIT 5
''')
print('')
print('   Por año (últimos 5):')
for row in cursor.fetchall():
    print(f'      {row[0]}: {row[1]:,}')

conn.close()
"

echo ""
echo "🎉 Proceso completado exitosamente"
echo ""
echo "💡 Tip: La base de datos SQLite está en boletines/normativas.db"

exit 0
