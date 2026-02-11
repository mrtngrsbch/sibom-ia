#!/bin/bash

# Script para actualizar datos en GitHub y forzar refresh del chatbot
# Uso: ./actualizar_datos_github.sh [mensaje_commit]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DATA="../sibom-data"
VERCEL_APP_URL="${VERCEL_APP_URL:-}"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  ACTUALIZACIÓN DE DATOS SIBOM → GitHub${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Paso 1: Generar base de datos SQLite
echo -e "${YELLOW}📋 Paso 1: Generando base de datos SQLite...${NC}"
cd "$SCRIPT_DIR"
python3 build_database.py
echo -e "${GREEN}✓ Base de datos generada${NC}"
echo ""

# Paso 2: Comprimir (opcional)
read -p "¿Comprimir archivos con gzip? (s/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo -e "${YELLOW}🗜️  Paso 2: Comprimiendo archivos...${NC}"
    python comprimir_boletines.py --keep-original
    echo -e "${GREEN}✓ Archivos comprimidos${NC}"
    USE_GZIP=true
else
    echo -e "${YELLOW}⏭️  Saltando compresión${NC}"
    USE_GZIP=false
fi
echo ""

# Paso 3: Copiar a repo de datos
if [ ! -d "$REPO_DATA" ]; then
    echo -e "${RED}❌ Error: No se encontró el directorio $REPO_DATA${NC}"
    echo -e "${YELLOW}   Primero clona tu repo de datos:${NC}"
    echo -e "${YELLOW}   git clone https://github.com/TU-USUARIO/sibom-data.git ../sibom-data${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 Paso 3: Copiando archivos a repo de datos...${NC}"
cd "$REPO_DATA"

if [ "$USE_GZIP" = true ]; then
    # Copiar archivos comprimidos
    cp "$SCRIPT_DIR"/boletines/*.json.gz ./boletines/ 2>/dev/null || true
    cp "$SCRIPT_DIR"/boletines/normativas.db.gz ./ 2>/dev/null || true
    echo -e "${GREEN}✓ Archivos .gz copiados (incluyendo normativas.db.gz)${NC}"
else
    # Copiar archivos sin comprimir
    cp "$SCRIPT_DIR"/boletines/*.json ./boletines/ 2>/dev/null || true
    cp "$SCRIPT_DIR"/boletines/normativas.db ./ 2>/dev/null || true
    echo -e "${GREEN}✓ Archivos copiados (incluyendo normativas.db)${NC}"
fi
echo ""

# Paso 4: Commit y push a GitHub
echo -e "${YELLOW}📤 Paso 4: Subiendo a GitHub...${NC}"

# Obtener estadísticas desde SQLite
TOTAL_DOCS=$(python3 -c "
import sqlite3
conn = sqlite3.connect('$SCRIPT_DIR/boletines/normativas.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM normativas')
print(cursor.fetchone()[0])
conn.close()
" 2>/dev/null || echo "N/A")

MUNICIPIOS=$(python3 -c "
import sqlite3
conn = sqlite3.connect('$SCRIPT_DIR/boletines/normativas.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(DISTINCT municipality) FROM normativas')
print(cursor.fetchone()[0])
conn.close()
" 2>/dev/null || echo "N/A")

# Mensaje de commit
DEFAULT_MSG="Update: $TOTAL_DOCS documentos ($MUNICIPIOS municipios) - $(date +%Y-%m-%d)"
COMMIT_MSG="${1:-$DEFAULT_MSG}"

git add .
git commit -m "$COMMIT_MSG" || echo -e "${YELLOW}⚠️  Sin cambios para commitear${NC}"
git push origin main

echo -e "${GREEN}✓ Push exitoso a GitHub${NC}"
echo ""

# Paso 5: Forzar refresh del chatbot en Vercel (opcional)
if [ -n "$VERCEL_APP_URL" ]; then
    echo -e "${YELLOW}🔄 Paso 5: Invalidando cache del chatbot...${NC}"
    RESPONSE=$(curl -s -X POST "$VERCEL_APP_URL/api/refresh" \
        -H "Content-Type: application/json" \
        -w "\n%{http_code}" | tail -1)

    if [ "$RESPONSE" -eq 200 ]; then
        echo -e "${GREEN}✓ Cache invalidado en Vercel${NC}"
    else
        echo -e "${YELLOW}⚠️  No se pudo invalidar cache (status: $RESPONSE)${NC}"
        echo -e "${YELLOW}   El cache se actualizará automáticamente en 5 minutos${NC}"
    fi
else
    echo -e "${YELLOW}ℹ️  Variable VERCEL_APP_URL no configurada${NC}"
    echo -e "${YELLOW}   Para invalidar cache automáticamente, exporta:${NC}"
    echo -e "${YELLOW}   export VERCEL_APP_URL=https://tu-app.vercel.app${NC}"
fi
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ ACTUALIZACIÓN COMPLETA${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "📊 Estadísticas:"
echo -e "   • Total documentos: $TOTAL_DOCS"
echo -e "   • Municipios: $MUNICIPIOS"
echo -e "   • Formato: $([ "$USE_GZIP" = true ] && echo "Gzip comprimido" || echo "JSON sin comprimir")"
echo ""
echo -e "🔗 Los datos estarán disponibles en el chatbot en ~5 minutos"
echo -e "   (o inmediatamente si usas webhook de GitHub)"
echo ""
