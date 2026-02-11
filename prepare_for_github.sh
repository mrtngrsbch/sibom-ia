#!/bin/bash
# prepare_for_github.sh
# Verifica y prepara el repo para push a GitHub (sin datos grandes)

set -e

echo "🔍 Verificando preparación para GitHub..."
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Verificar que .gitignore excluya datos
echo "📝 Verificando .gitignore..."
if grep -q "python-cli/boletines/\*.json" .gitignore; then
    echo -e "${GREEN}✓${NC} .gitignore correcto - excluye boletines"
else
    echo -e "${RED}✗${NC} .gitignore NO excluye boletines"
    echo "   Agrega: python-cli/boletines/*.json"
    exit 1
fi

if grep -q "dist/" .gitignore; then
    echo -e "${GREEN}✓${NC} .gitignore correcto - excluye dist/"
else
    echo -e "${RED}✗${NC} .gitignore NO excluye dist/"
    echo "   Agrega: dist/"
    exit 1
fi

# 2. Verificar que no haya archivos grandes staged
echo ""
echo "📦 Verificando archivos staged..."

LARGE_FILES=$(git ls-files --cached python-cli/boletines/*.json 2>/dev/null || true)
if [ -n "$LARGE_FILES" ]; then
    echo -e "${RED}✗${NC} Archivos de datos en staging:"
    echo "$LARGE_FILES"
    echo ""
    echo "Ejecuta: git rm --cached python-cli/boletines/*.json"
    exit 1
else
    echo -e "${GREEN}✓${NC} No hay archivos de datos en staging"
fi

DIST_FILES=$(git ls-files --cached python-cli/dist/ 2>/dev/null || true)
if [ -n "$DIST_FILES" ]; then
    echo -e "${RED}✗${NC} Archivos de dist/ en staging:"
    echo "$DIST_FILES"
    echo ""
    echo "Ejecuta: git rm --cached -r python-cli/dist/"
    exit 1
else
    echo -e "${GREEN}✓${NC} No hay archivos de dist/ en staging"
fi

# 3. Verificar tamaño del repo
echo ""
echo "📏 Verificando tamaño del repo..."
REPO_SIZE=$(du -sh .git | cut -f1)
echo "   Tamaño actual: $REPO_SIZE"

if [ -d "python-cli/boletines" ]; then
    BOLETINES_SIZE=$(du -sh python-cli/boletines 2>/dev/null | cut -f1 || echo "0B")
    echo "   Boletines (NO incluidos): $BOLETINES_SIZE"
fi

# 4. Verificar que archivos esenciales existan
echo ""
echo "📄 Verificando archivos esenciales..."

REQUIRED_FILES=(
    "chatbot/package.json"
    "chatbot/next.config.js"
    "chatbot/src/app/api/chat/route.ts"
    "python-cli/sibom_scraper.py"
    "python-cli/requirements.txt"
    "README.md"
    "DEPLOYMENT_GITHUB.md"
)

ALL_EXIST=true
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (FALTA)"
        ALL_EXIST=false
    fi
done

if [ "$ALL_EXIST" = false ]; then
    echo ""
    echo -e "${RED}Faltan archivos esenciales${NC}"
    exit 1
fi

# 5. Verificar que haya un remote de GitHub
echo ""
echo "🔗 Verificando remote de GitHub..."
REMOTE=$(git remote -v | grep origin | grep github.com | head -1 || echo "")

if [ -z "$REMOTE" ]; then
    echo -e "${YELLOW}⚠${NC}  No hay remote de GitHub configurado"
    echo ""
    echo "Configura con:"
    echo "  git remote add origin https://github.com/TU-USUARIO/sibom-scraper-assistant.git"
    echo ""
    read -p "¿Continuar de todas formas? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} Remote configurado:"
    echo "   $REMOTE"
fi

# 6. Resumen
echo ""
echo "============================================"
echo -e "${GREEN}✅ LISTO PARA GITHUB${NC}"
echo "============================================"
echo ""
echo "Archivos que serán incluidos en el commit:"
git status --short
echo ""
echo "Próximos pasos:"
echo "  1. git add ."
echo "  2. git commit -m \"feat: Preparar deployment con R2\""
echo "  3. git push origin main"
echo ""
echo "Archivos que NO se subirán (correcto):"
echo "  - python-cli/boletines/*.json (datos)"
echo "  - python-cli/dist/ (archivos comprimidos)"
echo "  - .env, .env.local (secrets)"
echo ""
echo "Los datos van a Cloudflare R2, no a GitHub."
