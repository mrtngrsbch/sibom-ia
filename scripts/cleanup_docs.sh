#!/bin/bash
# ============================================================
# SIBOM Docs Cleanup Script v1.0
# Fecha: 2026-02-06
# 
# Acciones:
#   1. Crea docs/archive/ para históricos
#   2. Mueve archivos redundantes a archive/
#   3. Elimina duplicados de .kiro/steering/
#   4. Conserva plans/ intacto
#
# USO: 
#   chmod +x scripts/cleanup_docs.sh
#   ./scripts/cleanup_docs.sh          # dry-run (muestra cambios)
#   ./scripts/cleanup_docs.sh --apply  # ejecuta cambios
# ============================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DRY_RUN=true
MOVED=0
DELETED=0

if [[ "${1:-}" == "--apply" ]]; then
    DRY_RUN=false
    echo "⚠️  MODO APLICAR — Los cambios son permanentes"
    echo "   Asegurate de haber commiteado antes."
    echo ""
    read -p "¿Continuar? (y/N): " confirm
    [[ "$confirm" =~ ^[Yy]$ ]] || exit 0
else
    echo "🔍 MODO DRY-RUN — Solo muestra cambios (usar --apply para ejecutar)"
    echo ""
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

do_move() {
    local from="$PROJECT_ROOT/$1" to="$PROJECT_ROOT/$2"
    if [[ -f "$from" ]]; then
        echo -e "  ${YELLOW}MOVER${NC}  $1 → $2"
        MOVED=$((MOVED + 1))
        if [[ "$DRY_RUN" == false ]]; then
            mkdir -p "$(dirname "$to")"
            mv "$from" "$to"
        fi
    else
        echo -e "  ${RED}SKIP${NC}   $1 (no existe)"
    fi
}

do_delete() {
    local file="$PROJECT_ROOT/$1"
    if [[ -f "$file" ]]; then
        echo -e "  ${RED}ELIMINAR${NC}  $1  ($2)"
        DELETED=$((DELETED + 1))
        if [[ "$DRY_RUN" == false ]]; then
            rm -f "$file"
        fi
    fi
}

# ═══ PASO 1: Crear estructura archive ═══
echo -e "\n${BLUE}═══ PASO 1: Crear docs/archive/ ═══${NC}\n"

for dir in "docs/archive/planning" "docs/archive/specs-originales" "docs/archive/experiments" "docs/archive/auditorias" "docs/archive/changelogs-root"; do
    echo -e "  ${GREEN}CREAR${NC}  $dir/"
    [[ "$DRY_RUN" == false ]] && mkdir -p "$PROJECT_ROOT/$dir"
done

# ═══ PASO 2: Root → archive (redundantes) ═══
echo -e "\n${BLUE}═══ PASO 2: Root → archive ═══${NC}\n"

do_move "CHANGELOG_OPTIMIZACIONES.md"   "docs/archive/changelogs-root/CHANGELOG_OPTIMIZACIONES.md"
do_move "CHANGELOG_REFACTOR_FILTROS.md" "docs/archive/changelogs-root/CHANGELOG_REFACTOR_FILTROS.md"
do_move "DOCKER_DEPLOYMENT.md"          "docs/archive/planning/DOCKER_DEPLOYMENT_ROOT.md"
do_move "MIGRACION.md"                  "docs/archive/planning/MIGRACION_ROOT.md"
do_move "AGENTS.md"                     "docs/archive/planning/AGENTS_ROOT.md"
do_move "IMPLEMENTATION_SUMMARY.md"     "docs/archive/planning/IMPLEMENTATION_SUMMARY.md"

# ═══ PASO 3: docs/ sueltos → archive ═══
echo -e "\n${BLUE}═══ PASO 3: docs/ sueltos → archive ═══${NC}\n"

# Specs originales (contradicciones: ChromaDB, OpenRouter)
do_move "docs/tech-spec-chatbot-legal.md"  "docs/archive/specs-originales/tech-spec-chatbot-legal.md"
do_move "docs/mvp-plan-chatbot-legal.md"   "docs/archive/specs-originales/mvp-plan-chatbot-legal.md"
do_move "docs/5-agentes-chatbot-legal.md"  "docs/archive/specs-originales/5-agentes-chatbot-legal.md"

# Auditoría → cubierta por plans/CODE_REVIEW.md
do_move "docs/AUDITORIA_CODIGO.md" "docs/archive/auditorias/AUDITORIA_CODIGO.md"

# Clima widget → experimental
do_move "docs/CLIMA_WIDGET.md"         "docs/archive/experiments/CLIMA_WIDGET.md"
do_move "docs/CLIMA_WIDGET_DISEÑO.md"  "docs/archive/experiments/CLIMA_WIDGET_DISEÑO.md"
do_move "docs/CLIMA_FIX_EMOJI_NOCHE.md" "docs/archive/experiments/CLIMA_FIX_EMOJI_NOCHE.md"

# Deployment redundante
do_move "docs/DEPLOYMENT_GITHUB_VERCEL.md" "docs/archive/planning/DEPLOYMENT_GITHUB_VERCEL.md"
do_move "docs/PROXIMOS_PASOS.md"           "docs/archive/planning/PROXIMOS_PASOS.md"

# Coding standards → .agents/steering/ lo cubre
do_move "docs/CODING_STANDARDS.md" "docs/archive/planning/CODING_STANDARDS.md"

# Actualización docs
do_move "docs/ACTUALIZACION_AUTOMATICA.md"  "docs/archive/planning/ACTUALIZACION_AUTOMATICA.md"
do_move "docs/ACTUALIZACION_DATOS.md"       "docs/archive/planning/ACTUALIZACION_DATOS.md"
do_move "docs/ACTUALIZACION_MUNICIPIOS.md"  "docs/archive/planning/ACTUALIZACION_MUNICIPIOS.md"

# UX, SIBOM data repo
do_move "docs/UX_MEJORAS_FILTROS.md"        "docs/archive/planning/UX_MEJORAS_FILTROS.md"
do_move "docs/SIBOM_DATA_REPO_README.md"    "docs/archive/planning/SIBOM_DATA_REPO_README.md"

# ═══ PASO 4: Eliminar .kiro/steering/ duplicados ═══
echo -e "\n${BLUE}═══ PASO 4: .kiro/steering/ duplicados ═══${NC}\n"

for file in .kiro/steering/error-handling.md .kiro/steering/performance-optimization.md \
            .kiro/steering/python-patterns.md .kiro/steering/testing-patterns.md \
            .kiro/steering/typescript-patterns.md; do
    do_delete "$file" "duplicado de .agents/steering/"
done

# ═══ PASO 5: Info sobre test outputs ═══
echo -e "\n${BLUE}═══ PASO 5: Test output .md ═══${NC}\n"
echo -e "  ${YELLOW}INFO${NC}  python-cli/tests/glm-ocr/*.md y tests/vision_models/*.md"
echo -e "         Son output de tests, no documentación. Considerar agregar a .gitignore"

# ═══ RESUMEN ═══
echo -e "\n${BLUE}═══════════════════════════════════════${NC}"
echo -e "${GREEN}RESUMEN:${NC}"
echo -e "  Archivos movidos:    ${MOVED}"
echo -e "  Archivos eliminados: ${DELETED}"
echo -e "  plans/:              ${GREEN}CONSERVADO${NC}"
echo ""
[[ "$DRY_RUN" == true ]] && echo -e "${YELLOW}Ejecutar con --apply para aplicar${NC}" || echo -e "${GREEN}✅ Cambios aplicados${NC}"
