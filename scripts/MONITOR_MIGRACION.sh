#!/bin/bash
# Monitor de Migración en Vivo - Notifica cuando termine

CHECKPOINT="/Users/mrtn/Documents/GitHub/sibom-scraper-assistant/python-cli/data/migration_checkpoint.json"
INTERVAL=5  # Check every 5 seconds

get_target() {
    python3 - << 'PY'
import json
from pathlib import Path

base = Path("/Users/mrtn/Documents/GitHub/sibom-scraper-assistant/python-cli/boletines")
count = 0
for path in base.glob("*/**/*Balances*.json"):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        continue
    if str(data.get("tipo_detalle", "")).strip().upper() == "BALANCE DE TESORERIA":
        count += 1
print(count)
PY
}

TARGET=$(get_target)

echo "═══════════════════════════════════════════════════════════"
echo "📊 MONITOR DE MIGRACIÓN QDRANT - BALANCE DE TESORERÍA"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "🎯 Target: $TARGET archivos"
echo "↻ Refresh: cada $INTERVAL segundos"
echo ""

get_progress() {
    if [ ! -f "$CHECKPOINT" ]; then
        echo "0:0:N/A"
        return
    fi
    
    PROCESSED=$(jq -r '.processed_files // 0' "$CHECKPOINT" 2>/dev/null)
    CHUNKS=$(jq -r '.processed_chunks // 0' "$CHECKPOINT" 2>/dev/null)
    UPDATED=$(jq -r '.last_updated // "N/A"' "$CHECKPOINT" 2>/dev/null)
    
    echo "$PROCESSED:$CHUNKS:$UPDATED"
}

print_progress() {
    local PROCESSED=$1
    local CHUNKS=$2
    local UPDATED=$3
    
    local REMAINING=$((TARGET - PROCESSED))
    local PERCENT=0
    if [ "$TARGET" -gt 0 ]; then
        PERCENT=$((PROCESSED * 100 / TARGET))
    fi
    
    # Progress bar (40 chars)
    local BAR_LEN=40
    local FILLED=0
    local EMPTY=$BAR_LEN
    if [ "$TARGET" -gt 0 ]; then
        FILLED=$((PROCESSED * BAR_LEN / TARGET))
        EMPTY=$((BAR_LEN - FILLED))
    fi
    
    local BAR=$(printf '█%.0s' {1..$FILLED})
    local EMPTY_BAR=$(printf '░%.0s' {1..$EMPTY})
    
    # Clear line and print
    clear
    echo "═══════════════════════════════════════════════════════════"
    echo "📊 MONITOR DE MIGRACIÓN QDRANT"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "📁 Archivos: $PROCESSED / $TARGET"
    echo "📦 Chunks: $CHUNKS"
    echo ""
    echo "[$BAR$EMPTY_BAR] $PERCENT%"
    echo ""
    echo "⏱️  Estadísticas:"
    echo "   Faltantes: $REMAINING archivos"
    if [ "$PROCESSED" -gt 0 ]; then
        CHUNKS_PER_FILE=$(echo "scale=1; $CHUNKS / $PROCESSED" | bc)
        echo "   Promedio: $CHUNKS_PER_FILE chunks/archivo"
        
        # Calcular ETA basado en rate actual
        ELAPSED_MINS=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${UPDATED:0:19}" "+%s" 2>/dev/null || echo "0")
        if [ "$ELAPSED_MINS" != "0" ]; then
            MIN_ELAPSED=$(( ($(date +%s) - ELAPSED_MINS) / 60 ))
            if [ "$MIN_ELAPSED" -gt 0 ]; then
                AVG_TIME_PER_FILE=$(echo "scale=1; $MIN_ELAPSED / $PROCESSED" | bc)
                ETA_SECS=$(echo "$REMAINING * $AVG_TIME_PER_FILE * 60" | bc)
                ETA_MINS=$(echo "scale=0; $ETA_SECS / 60" | bc)
                echo "   ETA: ~$ETA_MINS minutos"
            fi
        fi
    fi
    echo ""
    echo "🕐 Última actualización: $UPDATED"
    echo ""
}

LAST_PROCESSED=0

while true; do
    IFS=':' read -r PROCESSED CHUNKS UPDATED <<< "$(get_progress)"
    
    print_progress "$PROCESSED" "$CHUNKS" "$UPDATED"
    
    # Notificar si completó
    if [ "$TARGET" -gt 0 ] && [ "$PROCESSED" -eq "$TARGET" ] && [ "$PROCESSED" -gt 0 ]; then
        echo ""
        echo "╔════════════════════════════════════════════════════════╗"
        echo "║         ✅ MIGRACIÓN COMPLETADA EXITOSAMENTE            ║"
        echo "║           $PROCESSED archivos → $CHUNKS chunks          ║"
        echo "║      Ejecutar: bash POST_MIGRATION_CHECKLIST.sh        ║"
        echo "╚════════════════════════════════════════════════════════╝"
        echo ""
        
        # Sonido de alerta (si disponible en macOS)
        if command -v afplay &> /dev/null; then
            afplay /System/Library/Sounds/Glass.aiff 2>/dev/null
        fi

        # Notificacion de macOS (si disponible)
        if command -v osascript &> /dev/null; then
            osascript -e 'display notification "Migracion completada. Ejecuta POST_MIGRATION_CHECKLIST.sh" with title "Qdrant: Balances" sound name "Glass"'
        fi
        
        echo "🎉 ¡Puedes ejecutar la validación post-migración!"
        echo ""
        exit 0
    fi
    
    sleep $INTERVAL
done
