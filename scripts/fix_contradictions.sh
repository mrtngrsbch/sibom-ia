#!/bin/bash
# ============================================================
# SIBOM Docs Contradiction Fixer v2.0
# Fecha: 2026-02-06
#
# Escanea SOLO docs activos (no archive, no tool configs, no tests)
# y clasifica contradicciones como REALES vs LEGÍTIMAS
#
# USO:
#   chmod +x scripts/fix_contradictions.sh
#   ./scripts/fix_contradictions.sh          # escanear
#   ./scripts/fix_contradictions.sh --apply  # agregar notas de deprecación
# ============================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DRY_RUN=true
REAL_FIXES=0
LEGITIMATE=0

if [[ "${1:-}" == "--apply" ]]; then
    DRY_RUN=false
    echo "⚠️  MODO APLICAR"
    read -p "¿Continuar? (y/N): " confirm
    [[ "$confirm" =~ ^[Yy]$ ]] || exit 0
else
    echo "🔍 MODO ESCANEO"
    echo ""
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
GRAY='\033[0;90m'
NC='\033[0m'

# ============================================================
# SOLO archivos que importan (docs activos del proyecto)
# ============================================================
SCAN_DIRS=(
    "$PROJECT_ROOT/docs/01-architecture"
    "$PROJECT_ROOT/docs/02-deployment"
    "$PROJECT_ROOT/docs/03-features"
    "$PROJECT_ROOT/docs/04-changelogs"
    "$PROJECT_ROOT/docs/05-issues"
    "$PROJECT_ROOT/docs/06-reference"
    "$PROJECT_ROOT/chatbot/src/content"
    "$PROJECT_ROOT/chatbot/src/prompts"
    "$PROJECT_ROOT/chatbot/README.md"
    "$PROJECT_ROOT/python-cli/README.md"
    "$PROJECT_ROOT/python-cli/docs"
    "$PROJECT_ROOT/README.md"
)

# Archivos sueltos en docs/ que no están en subcarpetas
SCAN_LOOSE=(
    "$PROJECT_ROOT/docs/Municipios_contenidos.md"
    "$PROJECT_ROOT/docs/README.md"
)

find_active_docs() {
    for dir in "${SCAN_DIRS[@]}"; do
        if [[ -d "$dir" ]]; then
            find "$dir" -name "*.md" -type f
        elif [[ -f "$dir" ]]; then
            echo "$dir"
        fi
    done
    for file in "${SCAN_LOOSE[@]}"; do
        [[ -f "$file" ]] && echo "$file"
    done
}

scan_term() {
    local label="$1"
    local pattern="$2"
    local is_contradiction="$3"  # "real" o "check"
    
    echo -e "\n${YELLOW}🔍 $label${NC}"
    
    while IFS= read -r file; do
        relpath="${file#$PROJECT_ROOT/}"
        matches=$(grep -in "$pattern" "$file" 2>/dev/null || true)
        count=$(echo "$matches" | grep -c . 2>/dev/null || true)
        
        if [[ "$count" -gt 0 && -n "$matches" ]]; then
            if [[ "$is_contradiction" == "real" ]]; then
                echo -e "  ${RED}⚠ CONTRADICCIÓN${NC}  $relpath ($count)"
                # Mostrar líneas específicas
                echo "$matches" | head -3 | while IFS= read -r line; do
                    echo -e "    ${GRAY}$line${NC}"
                done
                REAL_FIXES=$((REAL_FIXES + count))
                
                # En modo apply: agregar nota de deprecación
                if [[ "$DRY_RUN" == false ]]; then
                    # Solo agregar si no tiene ya la nota
                    if ! head -1 "$file" | grep -q "⚠️ NOTA"; then
                        sed -i '' "1s|^|> ⚠️ NOTA (2026-02-06): Este doc puede tener refs desactualizadas. Stack actual: Gemini 3 Flash + GLM 4.7, Qdrant. Ver \`.agents/README.md\`\n\n|" "$file"
                        echo -e "    ${GREEN}→ Nota agregada${NC}"
                    fi
                fi
            else
                echo -e "  ${GRAY}✓ LEGÍTIMO${NC}    $relpath ($count) — verificar contexto"
                LEGITIMATE=$((LEGITIMATE + count))
            fi
        fi
    done < <(find_active_docs | sort -u)
}

echo -e "${BLUE}═══ Escaneando docs activos (no archive, no configs) ═══${NC}"

# --- CONTRADICCIONES REALES ---
scan_term "ChromaDB (debería ser Qdrant)" \
    "chromadb\|chroma.db\|chroma_db\|ChromaDB" \
    "real"

scan_term "pgvector/Supabase (debería ser Qdrant)" \
    "pgvector\|supabase" \
    "real"

scan_term "Gemini 2.5 Flash (debería ser Gemini 3 Flash)" \
    "gemini.2\.5\|gemini-2\.5\|Gemini 2.5" \
    "real"

# --- VERIFICAR CONTEXTO (pueden ser legítimas) ---
scan_term "OpenRouter (legítimo como provider, no como LLM)" \
    "openrouter\|OpenRouter" \
    "check"

scan_term "Anthropic/Claude (legítimo en configs de herramientas)" \
    "anthropic\|Anthropic" \
    "check"

# ═══ RESUMEN ═══
echo -e "\n${BLUE}═══════════════════════════════════════${NC}"
echo -e ""
echo -e "  ${RED}Contradicciones reales:${NC}  ${REAL_FIXES}"
echo -e "  ${GRAY}Menciones legítimas:${NC}    ${LEGITIMATE}"
echo -e ""
echo -e "${BLUE}Stack real (.agents/README.md):${NC}"
echo "  LLM:        Gemini 3 Flash + GLM 4.7 (via OpenRouter)"
echo "  Vector DB:  Qdrant"
echo "  Embeddings: text-embedding-3-small"
echo ""

if [[ "$REAL_FIXES" -eq 0 ]]; then
    echo -e "${GREEN}✅ No hay contradicciones reales en docs activos${NC}"
elif [[ "$DRY_RUN" == true ]]; then
    echo -e "${YELLOW}Ejecutar con --apply para agregar notas de deprecación a los ${REAL_FIXES} archivos${NC}"
else
    echo -e "${GREEN}✅ Notas de deprecación agregadas${NC}"
fi
