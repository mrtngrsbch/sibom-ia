#!/bin/bash
# Script para comparar la calidad de diferentes modelos LLM en SIBOM Scraper
# Uso: ./comparar_modelos.sh [URL_BOLETIN]

set -e

# URL por defecto (Boletín 98º de Carlos Tejedor)
URL="${1:-https://sibom.slyt.gba.gob.ar/bulletins/13556}"
BOLETIN_ID=$(echo "$URL" | sed 's/.*bulletins\///')

echo "╔════════════════════════════════════════════════════╗"
echo "║  🔬 Comparador de Modelos LLM - SIBOM Scraper     ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "📋 Boletín: $URL"
echo "🆔 ID: $BOLETIN_ID"
echo ""

# Crear directorio temporal para comparación
TEMP_DIR="comparacion_modelos_${BOLETIN_ID}"
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🆓 Modelo 1/4: z-ai/glm-4.5-air:free (GRATIS)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
START1=$(date +%s)
python3 ../sibom_scraper.py \
  --url "$URL" \
  --model z-ai/glm-4.5-air:free \
  --output modelo_free.json \
  --skip-existing
END1=$(date +%s)
TIEMPO1=$((END1 - START1))

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💰 Modelo 2/4: google/gemini-2.5-flash-lite (ECONÓMICO)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
START2=$(date +%s)
python3 ../sibom_scraper.py \
  --url "$URL" \
  --model google/gemini-2.5-flash-lite \
  --output modelo_lite.json \
  --skip-existing
END2=$(date +%s)
TIEMPO2=$((END2 - START2))

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚙️  Modelo 3/4: google/gemini-3-flash-preview (DEFAULT)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
START3=$(date +%s)
python3 ../sibom_scraper.py \
  --url "$URL" \
  --output modelo_default.json \
  --skip-existing
END3=$(date +%s)
TIEMPO3=$((END3 - START3))

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💎 Modelo 4/4: x-ai/grok-4.1-fast (PREMIUM)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
START4=$(date +%s)
python3 ../sibom_scraper.py \
  --url "$URL" \
  --model x-ai/grok-4.1-fast \
  --output modelo_premium.json \
  --skip-existing
END4=$(date +%s)
TIEMPO4=$((END4 - START4))

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║              📊 RESULTADOS COMPARATIVOS            ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Función para extraer estadísticas
extract_stats() {
  FILE=$1
  if [ ! -f "$FILE" ]; then
    echo "N/A"
    return
  fi

  # Contar palabras en fullText
  WORDS=$(cat "$FILE" | jq -r '.bulletins[0].fullText // .fullText // ""' | wc -w | tr -d ' ')

  # Contar caracteres
  CHARS=$(cat "$FILE" | jq -r '.bulletins[0].fullText // .fullText // ""' | wc -c | tr -d ' ')

  # Tamaño del archivo
  SIZE=$(ls -lh "$FILE" | awk '{print $5}')

  echo "$WORDS,$CHARS,$SIZE"
}

# Recopilar estadísticas
STATS1=$(extract_stats "modelo_free.json")
STATS2=$(extract_stats "modelo_lite.json")
STATS3=$(extract_stats "modelo_default.json")
STATS4=$(extract_stats "modelo_premium.json")

WORDS1=$(echo "$STATS1" | cut -d',' -f1)
WORDS2=$(echo "$STATS2" | cut -d',' -f1)
WORDS3=$(echo "$STATS3" | cut -d',' -f1)
WORDS4=$(echo "$STATS4" | cut -d',' -f1)

CHARS1=$(echo "$STATS1" | cut -d',' -f2)
CHARS2=$(echo "$STATS2" | cut -d',' -f2)
CHARS3=$(echo "$STATS3" | cut -d',' -f3)
CHARS4=$(echo "$STATS4" | cut -d',' -f3)

SIZE1=$(echo "$STATS1" | cut -d',' -f3)
SIZE2=$(echo "$STATS2" | cut -d',' -f3)
SIZE3=$(echo "$STATS3" | cut -d',' -f3)
SIZE4=$(echo "$STATS4" | cut -d',' -f3)

# Tabla de resultados
echo "┌────────────────────────────┬───────┬───────────┬────────┬─────────┐"
echo "│ Modelo                     │ Tiempo│ Palabras  │ Chars  │ Tamaño  │"
echo "├────────────────────────────┼───────┼───────────┼────────┼─────────┤"
printf "│ %-26s │ %5ss │ %9s │ %6s │ %7s │\n" "glm-4.5-air:free" "$TIEMPO1" "$WORDS1" "$CHARS1" "$SIZE1"
printf "│ %-26s │ %5ss │ %9s │ %6s │ %7s │\n" "gemini-2.5-flash-lite" "$TIEMPO2" "$WORDS2" "$CHARS2" "$SIZE2"
printf "│ %-26s │ %5ss │ %9s │ %6s │ %7s │\n" "gemini-3-flash-preview" "$TIEMPO3" "$WORDS3" "$CHARS3" "$SIZE3"
printf "│ %-26s │ %5ss │ %9s │ %6s │ %7s │\n" "grok-4.1-fast" "$TIEMPO4" "$WORDS4" "$CHARS4" "$SIZE4"
echo "└────────────────────────────┴───────┴───────────┴────────┴─────────┘"

echo ""
echo "📂 Archivos generados en: $TEMP_DIR/"
echo ""
echo "🔍 Comandos útiles para inspección:"
echo ""
echo "# Ver texto extraído (primeras 50 líneas)"
echo "cat $TEMP_DIR/modelo_free.json | jq -r '.bulletins[0].fullText' | head -50"
echo "cat $TEMP_DIR/modelo_lite.json | jq -r '.bulletins[0].fullText' | head -50"
echo "cat $TEMP_DIR/modelo_default.json | jq -r '.bulletins[0].fullText' | head -50"
echo "cat $TEMP_DIR/modelo_premium.json | jq -r '.bulletins[0].fullText' | head -50"
echo ""
echo "# Comparar diferencias entre modelos"
echo "diff <(jq -r '.bulletins[0].fullText' $TEMP_DIR/modelo_free.json) \\"
echo "     <(jq -r '.bulletins[0].fullText' $TEMP_DIR/modelo_default.json)"
echo ""
echo "# Buscar artículos específicos"
echo "cat $TEMP_DIR/modelo_default.json | jq -r '.bulletins[0].fullText' | grep -i 'ARTICULO'"
echo ""

cd ..

echo "✅ Comparación completada."
