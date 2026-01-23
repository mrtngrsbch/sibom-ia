#!/bin/bash

# Script para reiniciar el scraping desde cero
# Este script hace un backup de los boletines existentes, los elimina y re-scrapea todo

set -e  # Detener el script si hay algún error

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="python-cli/boletines_backup_${BACKUP_DATE}"
BULLETINS_DIR="python-cli/boletines"
INDEX_FILE="python-cli/boletines_index.json"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        🔄 SIBOM Scraper - Reinicio Completo                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Paso 1: Hacer backup
echo "📦 Paso 1/4: Creando backup de seguridad..."
if [ -d "$BULLETINS_DIR" ] || [ -f "$INDEX_FILE" ]; then
    mkdir -p "$BACKUP_DIR"
    if [ -d "$BULLETINS_DIR" ]; then
        cp -r "$BULLETINS_DIR" "$BACKUP_DIR/"
        echo "✓ Boletines respaldados en: $BACKUP_DIR"
    fi
    if [ -f "$INDEX_FILE" ]; then
        cp "$INDEX_FILE" "$BACKUP_DIR/"
        echo "✓ Índice respaldado en: $BACKUP_DIR"
    fi
else
    echo "⚠ No hay boletines existentes para respaldar"
fi
echo ""

# Paso 2: Eliminar boletines
echo "🗑️  Paso 2/4: Eliminando boletines existentes..."
if [ -d "$BULLETINS_DIR" ]; then
    rm -rf "$BULLETINS_DIR"
    echo "✓ Directorio de boletines eliminado"
fi
if [ -f "$INDEX_FILE" ]; then
    rm "$INDEX_FILE"
    echo "✓ Índice eliminado"
fi
echo ""

# Paso 3: Re-crear directorio
echo "📁 Paso 3/4: Re-creando directorio de boletines..."
mkdir -p "$BULLETINS_DIR"
echo "✓ Directorio listo: $BULLETINS_DIR"
echo ""

# Paso 4: Re-scrapear
echo "🚀 Paso 4/4: Iniciando scraping desde cero..."
echo ""
echo "   Este proceso puede tomar tiempo dependiendo de la cantidad de boletines."
echo "   El scraper usará BeautifulSoup (sin LLM) para extraer el texto completo."
echo ""
read -p "   ¿Deseas continuar? (s/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Ss]$ ]]; then
    cd python-cli
    python sibom_scraper.py https://sibom.slyt.gba.gob.ar/cities/22 --skip-existing=false
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║        ✅ Scraping completado                                   ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📊 Resumen:"
    echo "   - Backup guardado en: ../$BACKUP_DIR"
    echo "   - Nuevos boletines en: boletines/"
    echo ""
    echo "💡 Si encuentras algún problema, puedes restaurar el backup con:"
    echo "   cp -r ../$BACKUP_DIR/* boletines/"
else
    echo ""
    echo "❌ Proceso cancelado por el usuario."
    echo "💡 Los boletines fueron eliminados pero no se re-scrapearon."
    echo "   Puedes restaurar el backup con: cp -r $BACKUP_DIR/* $BULLETINS_DIR/"
    exit 1
fi
