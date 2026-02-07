#!/bin/bash
# ============================================================
# SIBOM Docs Contradiction Fixer v1.0
# Fecha: 2026-02-06
#
# Corrige contradicciones arquitectónicas en docs existentes:
#   - LLM: OpenRouter/Claude → Gemini 3 Flash + GLM 4.7
#   - Vector DB: ChromaDB/pgvector → Qdrant  
#   - Otras inconsistencias
#
# USO:
#   chmod +x scripts/fix_contradictions.sh
#   ./scripts/fix_contradictions.sh          # dry-run
#   ./scripts/fix_contradictions.sh --apply  # ejecutar
# ============================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DRY_RUN=true
FIXES=0

if [[ "${1:-}" == "--apply" ]]; then
    DRY_RUN=false
    echo "⚠️  MODO APLICAR"
    read -p "¿Continuar? (y/N): " confirm
    [[ "$confirm" =~ ^[Yy]$ ]] || exit 0
else
    echo "🔍 MODO DRY-RUN"
    echo ""
fi

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Find files with contradictions (excluding archive, node_modules, venv, .git)
find_docs() {
    find "$PROJECT_ROOT" \
        -name "*.md" \
        -not -path "*/node_modules/*" \
        -not -path "*/.git/*" \
        -not -path "*/venv/*" \
        -not -path "*/.venv/*" \
        -not -path "*/archive/*" \
        -not -path "*/.agents/*" \
        -type f
}

echo -e "\n${BLUE}═══ Buscando contradicciones ═══${NC}\n"

# --- ChromaDB references ---
echo -e "${YELLOW}🔍 ChromaDB → Qdrant${NC}"
while IFS= read -r file; do
    relpath="${file#$PROJECT_ROOT/}"
    count=$(grep -ci "chromadb\|chroma db\|chroma_db" "$file" 2>/dev/null || true)
    if [[ "$count" -gt 0 ]]; then
        echo -e "  ${YELLOW}ENCONTRADO${NC} $relpath ($count menciones)"
        FIXES=$((FIXES + count))
        if [[ "$DRY_RUN" == false ]]; then
            # Add deprecation notice at top
            sed -i '' '1s/^/> ⚠️ NOTA: Este documento puede contener referencias a ChromaDB que están desactualizadas. La Vector DB actual es **Qdrant**.\n\n/' "$file"
        fi
    fi
done < <(find_docs)

# --- OpenRouter as primary LLM ---
echo -e "\n${YELLOW}🔍 OpenRouter como LLM principal${NC}"
while IFS= read -r file; do
    relpath="${file#$PROJECT_ROOT/}"
    count=$(grep -ci "openrouter" "$file" 2>/dev/null || true)
    if [[ "$count" -gt 0 ]]; then
        echo -e "  ${YELLOW}ENCONTRADO${NC} $relpath ($count menciones)"
        FIXES=$((FIXES + count))
    fi
done < <(find_docs)

# --- pgvector/Supabase as vector DB ---
echo -e "\n${YELLOW}🔍 pgvector/Supabase como Vector DB${NC}"
while IFS= read -r file; do
    relpath="${file#$PROJECT_ROOT/}"
    count=$(grep -ci "pgvector\|supabase" "$file" 2>/dev/null || true)
    if [[ "$count" -gt 0 ]]; then
        echo -e "  ${YELLOW}ENCONTRADO${NC} $relpath ($count menciones)"
        FIXES=$((FIXES + count))
    fi
done < <(find_docs)

# --- Anthropic Claude as extraction LLM ---
echo -e "\n${YELLOW}🔍 Anthropic Claude como LLM de extracción${NC}"
while IFS= read -r file; do
    relpath="${file#$PROJECT_ROOT/}"
    # Exclude references that are about Claude Code/IDE, only flag Claude as extraction LLM
    count=$(grep -ci "anthropic\|claude" "$file" 2>/dev/null || true)
    if [[ "$count" -gt 0 ]]; then
        # Check if it's a tool config file (these legitimately reference Claude)
        if [[ "$relpath" != ".claude/"* && "$relpath" != *"CLAUDE.md" && "$relpath" != *"system.md" ]]; then
            echo -e "  ${YELLOW}REVISAR${NC}  $relpath ($count menciones — verificar contexto)"
        fi
    fi
done < <(find_docs)

# ═══ RESUMEN ═══
echo -e "\n${BLUE}═══════════════════════════════════════${NC}"
echo -e "${GREEN}RESUMEN:${NC}"
echo -e "  Contradicciones encontradas: ${FIXES}"
echo ""
echo -e "${BLUE}Stack real (fuente: .agents/README.md):${NC}"
echo "  LLM principal:    Gemini 3 Flash"
echo "  LLM alternativo:  GLM 4.7"
echo "  Vector DB:        Qdrant"
echo "  Embeddings:       text-embedding-3-small"
echo "  Storage:          Cloudflare R2"
echo "  Frontend deploy:  Vercel"
echo ""

if [[ "$DRY_RUN" == true ]]; then
    echo -e "${YELLOW}Ejecutar con --apply para agregar notas de deprecación${NC}"
    echo -e "${YELLOW}Los archivos más problemáticos ya se mueven a archive/ con cleanup_docs.sh${NC}"
else
    echo -e "${GREEN}✅ Notas de deprecación agregadas${NC}"
fi
