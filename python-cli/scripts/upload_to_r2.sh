#!/bin/bash
# upload_to_r2.sh
# Sube archivos comprimidos a Cloudflare R2 usando wrangler

set -e

BUCKET_NAME="sibom-data"
DIST_DIR="dist"

echo "🚀 Subiendo archivos a R2 bucket: $BUCKET_NAME"
echo ""

# Verificar que wrangler esté instalado
if ! command -v wrangler &> /dev/null; then
    echo "❌ Wrangler no está instalado"
    echo "Instala con: pnpm add -g wrangler"
    exit 1
fi

# Verificar que estés logueado
if ! wrangler whoami &> /dev/null; then
    echo "❌ No estás logueado en Cloudflare"
    echo "Ejecuta: wrangler login"
    exit 1
fi

# 1. Subir índice
echo "📋 Subiendo índice de normativas..."
wrangler r2 object put "$BUCKET_NAME/normativas_index_minimal.json.gz" \
  --file "$DIST_DIR/normativas_index_minimal.json.gz"
echo "✅ Índice subido"
echo ""

# 2. Subir boletines
echo "📦 Subiendo boletines..."
total=$(ls "$DIST_DIR/boletines"/*.gz 2>/dev/null | wc -l)
echo "Total de archivos: $total"
echo ""

count=0
for file in "$DIST_DIR/boletines"/*.gz; do
    filename=$(basename "$file")
    count=$((count + 1))

    echo "[$count/$total] $filename"
    wrangler r2 object put "$BUCKET_NAME/boletines/$filename" --file "$file"
done

echo ""
echo "============================================"
echo "✅ UPLOAD COMPLETADO"
echo "============================================"
echo ""
echo "Archivos subidos:"
echo "  - normativas_index_minimal.json.gz"
echo "  - $total boletines"
echo ""
echo "Próximo paso: Configurar Vercel"
