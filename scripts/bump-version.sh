#!/bin/bash

# Script para automatizar el proceso de bump de versión
# Uso: ./scripts/bump-version.sh [major|minor|patch]

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio raíz del proyecto
if [ ! -f "chatbot/package.json" ]; then
  echo -e "${RED}Error: Debe ejecutar este script desde el directorio raíz del proyecto${NC}"
  exit 1
fi

# Verificar que se pasó un argumento
if [ -z "$1" ]; then
  echo -e "${RED}Error: Debe especificar el tipo de bump (major, minor, patch)${NC}"
  echo "Uso: $0 [major|minor|patch]"
  exit 1
fi

BUMP_TYPE=$1

# Validar tipo de bump
if [[ ! "$BUMP_TYPE" =~ ^(major|minor|patch)$ ]]; then
  echo -e "${RED}Error: Tipo de bump inválido. Use: major, minor, o patch${NC}"
  exit 1
fi

# Verificar que no hay cambios sin commit
if [ -n "$(git status --porcelain)" ]; then
  echo -e "${YELLOW}Advertencia: Hay cambios sin commit${NC}"
  echo "Archivos modificados:"
  git status --short
  echo ""
  read -p "¿Desea continuar? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# Obtener versión actual
CURRENT_VERSION=$(node -p "require('./chatbot/package.json').version")
echo -e "${GREEN}Versión actual: ${CURRENT_VERSION}${NC}"

# Calcular nueva versión
IFS='.' read -r -a VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR="${VERSION_PARTS[0]}"
MINOR="${VERSION_PARTS[1]}"
PATCH="${VERSION_PARTS[2]}"

case $BUMP_TYPE in
  major)
    MAJOR=$((MAJOR + 1))
    MINOR=0
    PATCH=0
    ;;
  minor)
    MINOR=$((MINOR + 1))
    PATCH=0
    ;;
  patch)
    PATCH=$((PATCH + 1))
    ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
echo -e "${GREEN}Nueva versión: ${NEW_VERSION}${NC}"

# Confirmar cambio
read -p "¿Confirmar bump de versión? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Operación cancelada"
  exit 0
fi

# Actualizar package.json
echo -e "${YELLOW}Actualizando chatbot/package.json...${NC}"
node << EOF
const fs = require('fs');
const packageJson = require('./chatbot/package.json');
packageJson.version = '${NEW_VERSION}';
fs.writeFileSync('./chatbot/package.json', JSON.stringify(packageJson, null, 2) + '\n');
EOF

# Verificar que CHANGELOG existe
if [ ! -f "CHANGELOG.md" ]; then
  echo -e "${RED}Error: CHANGELOG.md no existe${NC}"
  exit 1
fi

# Agregar entrada al CHANGELOG
echo -e "${YELLOW}Actualizando CHANGELOG.md...${NC}"
TODAY=$(date +%Y-%m-%d)
CHANGELOG_ENTRY="## [${NEW_VERSION}] - ${TODAY}

### Agregado
- TODO: Describir nuevas funcionalidades

### Mejorado
- TODO: Describir mejoras

### Corregido
- TODO: Describir correcciones

---

"

# Insertar entrada después de [Unreleased]
sed -i.bak "/## \[Unreleased\]/a\\
$CHANGELOG_ENTRY" CHANGELOG.md

rm -f CHANGELOG.md.bak

echo -e "${GREEN}✓ CHANGELOG.md actualizado${NC}"

# Crear commit
echo -e "${YELLOW}Creando commit...${NC}"
git add chatbot/package.json CHANGELOG.md
git commit -m "chore: bump version to ${NEW_VERSION}

- Actualizar package.json a v${NEW_VERSION}
- Actualizar CHANGELOG.md con sección para v${NEW_VERSION}

Tipo de bump: ${BUMP_TYPE}
Versión anterior: v${CURRENT_VERSION}
Versión nueva: v${NEW_VERSION}"

echo -e "${GREEN}✓ Commit creado${NC}"

# Crear tag
echo -e "${YELLOW}Creando tag v${NEW_VERSION}...${NC}"
git tag -a "v${NEW_VERSION}" -m "Release v${NEW_VERSION}

Ver CHANGELOG.md para detalles de cambios."

echo -e "${GREEN}✓ Tag creado${NC}"

# Mostrar próximos pasos
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}¡Versión bumpeada exitosamente!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Próximos pasos:"
echo ""
echo "1. Editar CHANGELOG.md para completar los TODO con cambios reales:"
echo "   nano CHANGELOG.md"
echo ""
echo "2. Hacer push de los cambios:"
echo "   git push origin main"
echo ""
echo "3. Hacer push del tag para crear el release:"
echo "   git push origin v${NEW_VERSION}"
echo ""
echo "4. GitHub Actions creará automáticamente el release en:"
echo "   https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/releases"
echo ""
echo -e "${YELLOW}IMPORTANTE:${NC} Asegúrate de actualizar el CHANGELOG con cambios reales antes del push"
