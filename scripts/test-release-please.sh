#!/bin/bash

# Script de test para Release Please
# Simula el workflow completo sin hacer push real

set -e

echo "🧪 Testing Release Please Configuration"
echo "=========================================="
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Verificar archivos de configuración
echo "1️⃣ Verificando archivos de configuración..."

if [ -f ".release-please-manifest.json" ]; then
  echo -e "${GREEN}✓${NC} .release-please-manifest.json encontrado"
  cat .release-please-manifest.json | jq .
else
  echo -e "${RED}✗${NC} .release-please-manifest.json no encontrado"
  exit 1
fi

echo ""

if [ -f "release-please-config.json" ]; then
  echo -e "${GREEN}✓${NC} release-please-config.json encontrado"
  cat release-please-config.json | jq .packages
else
  echo -e "${RED}✗${NC} release-please-config.json no encontrado"
  exit 1
fi

echo ""

if [ -f ".github/workflows/release-please.yml" ]; then
  echo -e "${GREEN}✓${NC} GitHub Action configurado"
else
  echo -e "${RED}✗${NC} .github/workflows/release-please.yml no encontrado"
  exit 1
fi

echo ""
echo "2️⃣ Verificando versión actual..."

CURRENT_VERSION=$(node -p "require('./chatbot/package.json').version")
echo -e "Versión en package.json: ${GREEN}${CURRENT_VERSION}${NC}"

MANIFEST_VERSION=$(cat .release-please-manifest.json | jq -r '."."')
echo -e "Versión en manifest: ${GREEN}${MANIFEST_VERSION}${NC}"

if [ "$CURRENT_VERSION" != "$MANIFEST_VERSION" ]; then
  echo -e "${YELLOW}⚠${NC} Las versiones no coinciden. Sincronizando..."
  jq --arg version "$CURRENT_VERSION" '."."] = $version' .release-please-manifest.json > .release-please-manifest.json.tmp
  mv .release-please-manifest.json.tmp .release-please-manifest.json
  echo -e "${GREEN}✓${NC} Sincronizado a ${CURRENT_VERSION}"
fi

echo ""
echo "3️⃣ Analizando commits desde último tag..."

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
  echo -e "${YELLOW}⚠${NC} No hay tags previos"
  COMMITS=$(git log --oneline --all | head -10)
else
  echo -e "Último tag: ${GREEN}${LAST_TAG}${NC}"
  COMMITS=$(git log --oneline ${LAST_TAG}..HEAD)
fi

if [ -z "$COMMITS" ]; then
  echo -e "${YELLOW}⚠${NC} No hay commits nuevos desde ${LAST_TAG}"
else
  echo ""
  echo "Commits nuevos:"
  echo "$COMMITS" | while read line; do
    if echo "$line" | grep -q "^[a-f0-9]* feat"; then
      echo -e "  ${GREEN}✨${NC} $line"
    elif echo "$line" | grep -q "^[a-f0-9]* fix"; then
      echo -e "  ${RED}🐛${NC} $line"
    elif echo "$line" | grep -q "^[a-f0-9]* docs"; then
      echo -e "  📚 $line"
    else
      echo -e "  $line"
    fi
  done
fi

echo ""
echo "4️⃣ Prediciendo próximo bump..."

HAS_BREAKING=false
HAS_FEAT=false
HAS_FIX=false

if [ ! -z "$COMMITS" ]; then
  if echo "$COMMITS" | grep -qE "(^[a-f0-9]* feat!|BREAKING CHANGE)"; then
    HAS_BREAKING=true
  fi
  if echo "$COMMITS" | grep -q "^[a-f0-9]* feat"; then
    HAS_FEAT=true
  fi
  if echo "$COMMITS" | grep -q "^[a-f0-9]* fix"; then
    HAS_FIX=true
  fi
fi

IFS='.' read -r -a VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR="${VERSION_PARTS[0]}"
MINOR="${VERSION_PARTS[1]}"
PATCH="${VERSION_PARTS[2]}"

if [ "$HAS_BREAKING" = true ]; then
  NEXT_VERSION="$((MAJOR + 1)).0.0"
  BUMP_TYPE="${RED}MAJOR${NC}"
elif [ "$HAS_FEAT" = true ]; then
  NEXT_VERSION="${MAJOR}.$((MINOR + 1)).0"
  BUMP_TYPE="${YELLOW}MINOR${NC}"
elif [ "$HAS_FIX" = true ]; then
  NEXT_VERSION="${MAJOR}.${MINOR}.$((PATCH + 1))"
  BUMP_TYPE="${GREEN}PATCH${NC}"
else
  NEXT_VERSION="${CURRENT_VERSION}"
  BUMP_TYPE="${YELLOW}NO BUMP${NC} (solo docs/chore)"
fi

echo -e "Bump type: ${BUMP_TYPE}"
echo -e "Próxima versión: ${GREEN}${NEXT_VERSION}${NC}"

echo ""
echo "5️⃣ Verificando Conventional Commits..."

if [ ! -z "$COMMITS" ]; then
  UNCONVENTIONAL=$(echo "$COMMITS" | grep -vE "^[a-f0-9]* (feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?:" || true)
  
  if [ ! -z "$UNCONVENTIONAL" ]; then
    echo -e "${RED}✗${NC} Commits no convencionales encontrados:"
    echo "$UNCONVENTIONAL" | while read line; do
      echo -e "  ${RED}!${NC} $line"
    done
    echo ""
    echo -e "${YELLOW}Recomendación:${NC} Usar formato: tipo(scope): descripción"
    echo "Ejemplo: feat(chat): agregar nuevo filtro"
  else
    echo -e "${GREEN}✓${NC} Todos los commits siguen Conventional Commits"
  fi
fi

echo ""
echo "=========================================="
echo "📋 Resumen"
echo "=========================================="
echo -e "Versión actual:    ${GREEN}${CURRENT_VERSION}${NC}"
echo -e "Próxima versión:   ${GREEN}${NEXT_VERSION}${NC}"
echo -e "Tipo de bump:      ${BUMP_TYPE}"
echo -e "Commits nuevos:    $(echo "$COMMITS" | wc -l | xargs)"
echo ""

if [ "$NEXT_VERSION" != "$CURRENT_VERSION" ]; then
  echo -e "${GREEN}✓${NC} Release Please creará/actualizará PR cuando pushees a main"
  echo ""
  echo "Próximos pasos:"
  echo "1. git push origin main"
  echo "2. Esperar a que GitHub Actions cree el PR"
  echo "3. Revisar el PR: gh pr list --label 'autorelease: pending'"
  echo "4. Merge cuando quieras release: gh pr merge <numero> --squash"
else
  echo -e "${YELLOW}⚠${NC} No hay cambios que requieran release"
  echo ""
  echo "Para crear un release, hacer commits con:"
  echo "  • feat: para nueva funcionalidad (MINOR bump)"
  echo "  • fix: para correcciones (PATCH bump)"
  echo "  • feat! o BREAKING CHANGE para breaking changes (MAJOR bump)"
fi

echo ""
echo "🎉 Test completado!"
