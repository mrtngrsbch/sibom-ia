#!/bin/bash
# update.sh - Actualización del proyecto en VPS
# Uso: ./update.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  SIBOM - Actualización${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

cd "$HOME/sibom-scraper-assistant"

# Pull de cambios
echo -e "${YELLOW}Obteniendo últimos cambios...${NC}"
git pull origin main

# Reconstruir y reiniciar
echo -e "${YELLOW}Reconstruyendo contenedores...${NC}"
docker-compose up -d --build

echo ""
echo -e "${GREEN}✅ Actualización completada${NC}"
echo ""
echo -e "Ver logs: docker-compose logs -f"
