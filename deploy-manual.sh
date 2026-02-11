#!/bin/bash
# deploy-manual.sh - Guía paso a paso para despliegue manual
# Este script NO ejecuta comandos destructivos, solo muestra instrucciones

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DOMAIN="mangrullo.microagencia.com"
IP="89.116.49.63"
USER="root"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  SIBOM - Guía de Despliegue Manual${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo -e "Dominio: ${YELLOW}${DOMAIN}${NC}"
echo -e "IP VPS:   ${YELLOW}${IP}${NC}"
echo ""

echo -e "${BLUE}╔═════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  PASO 1: Conectarte al VPS                       ║${NC}"
echo -e "${BLUE}╚═════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Ejecutá en tu terminal local:"
echo -e "${YELLOW}ssh ${USER}@${IP}${NC}"
echo ""

sleep 1

echo -e "${BLUE}╔═════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  PASO 2: Clonar repositorio                        ║${NC}"
echo -e "${BLUE}╚═════════════════════════════════════════════════╝${NC}"
echo ""
echo "cd ~"
echo "git clone https://github.com/mrtngrsbch/sibom-scraper-assistant.git"
echo "cd sibom-scraper-assistant"
echo ""

sleep 1

echo -e "${BLUE}╔═════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  PASO 3: Configurar .env                             ║${NC}"
echo -e "${BLUE}╚═════════════════════════════════════════════════╝${NC}"
echo ""
echo "nano .env"
echo ""
echo "Pegá estas variables (reemplazá TU_KEY con tu API key real):"
echo -e "${GREEN}NODE_ENV=production${NC}"
echo -e "${GREEN}OPENROUTER_API_KEY=TU_KEY${NC}"
echo -e "${GREEN}LLM_MODEL_PRIMARY=google/gemini-3-flash-preview${NC}"
echo -e "${GREEN}SAT_API_URL=http://sat-analysis:8001${NC}"
echo -e "${GREEN}USE_NORMATIVAS_INDEX=true${NC}"
echo -e "${GREEN}USE_SQLITE=true${NC}"
echo ""

sleep 1

echo -e "${BLUE}╔═════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  PASO 4: Usar Docker Manager de Hostinger          ║${NC}"
echo -e "${BLUE}╚═════════════════════════════════════════════════╝${NC}"
echo ""
echo "1. Entrá a hPanel → Docker → Docker Manager"
echo "2. Creá 3 contenedores:"
echo ""
echo -e "${YELLOW}   chatbot:${NC}"
echo "   - Image: (dejar vacío para build)"
echo "   - Puerto: 3000:3000"
echo "   - Env: NODE_ENV=production, SAT_API_URL=http://sat-analysis:8001"
echo ""
echo -e "${YELLOW}   sat-analysis:${NC}"
echo "   - Image: (dejar vacío)"
echo "   - Puerto: 8001:8001"
echo "   - Volumes: sat-data:/app/data, sat-cache:/app/cache"
echo ""
echo -e "${YELLOW}   nginx:${NC}"
echo "   - Image: nginx:alpine"
echo "   - Puertos: 80:80, 443:443"
echo "   - Volume: ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro"
echo ""

sleep 1

echo -e "${BLUE}╔═════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  PASO 5: Configurar SSL (Let's Encrypt)          ║${NC}"
echo -e "${BLUE}╚═════════════════════════════════════════════════╝${NC}"
echo ""
echo "1. hPanel → SSL → Let's Encrypt"
echo "2. Seleccioná: ${YELLOW}mangrullo.microagencia.com${NC}"
echo "3. Click en 'Obtener Certificado'"
echo ""

sleep 1

echo -e "${BLUE}╔═════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  PASO 6: Verificar                                 ║${NC}"
echo -e "${BLUE}╚═════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}curl https://${DOMAIN}${NC}"
echo ""

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  ¡Listo! Tu aplicación estará en:${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "  🌐 https://${DOMAIN}"
echo ""

echo -e "${BLUE}Comandos útiles (ejecutar en el VPS):${NC}"
echo ""
echo -e "${GREEN}docker ps${NC}                # Ver contenedores"
echo -e "${GREEN}docker logs sibom-chatbot    # Ver logs chatbot${NC}"
echo -e "${GREEN}docker restart sibom-chatbot # Reiniciar${NC}"
echo ""
