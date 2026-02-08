#!/bin/bash
# Control de servicios de desarrollo con Overmind
# Uso: ./scripts/devctl.sh {start|stop|restart|status|logs} [servicio]

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Verificar que Overmind está instalado
if ! command -v overmind &> /dev/null; then
    echo -e "${RED}❌ Overmind no está instalado${NC}"
    echo -e "${YELLOW}   Instala con: brew install tmux overmind${NC}"
    exit 1
fi

case "$1" in
    start)
        echo -e "${BLUE}🚀 Iniciando servicios...${NC}"
        overmind start
        ;;
    stop)
        echo -e "${YELLOW}🛑 Deteniendo servicios...${NC}"
        overmind stop
        echo -e "${GREEN}✅ Servicios detenidos${NC}"
        ;;
    restart)
        if [ -z "$2" ]; then
            echo -e "${YELLOW}🔄 Reiniciando todos los servicios...${NC}"
            overmind restart
        else
            echo -e "${YELLOW}🔄 Reiniciando $2...${NC}"
            overmind restart $2
        fi
        ;;
    status)
        echo -e "${BLUE}📊 Estado de servicios:${NC}"
        echo ""
        overmind status
        ;;
    logs)
        if [ -z "$2" ]; then
            echo -e "${BLUE}📄 Mostrando logs de todos los servicios (Ctrl+C para salir)${NC}"
            overmind logs
        else
            echo -e "${BLUE}📄 Mostrando logs de $2 (Ctrl+C para salir)${NC}"
            overmind logs $2
        fi
        ;;
    connect)
        # Conectar a la sesión de tmux de Overmind directamente
        if [ -z "$2" ]; then
            echo -e "${BLUE}🔌 Conectando a la sesión de Overmind${NC}"
            overmind connect
        else
            echo -e "${BLUE}🔌 Conectando al servicio $2${NC}"
            overmind connect $2
        fi
        ;;
    *)
        echo -e "${BLUE}SIBOM Dev Control${NC}"
        echo ""
        echo "Uso: devctl {comando} [servicio]"
        echo ""
        echo -e "${GREEN}Comandos:${NC}"
        echo "  start           - Inicia todos los servicios"
        echo "  stop            - Detiene todos los servicios"
        echo "  restart [srv]   - Reinicia todos o un servicio específico"
        echo "  status          - Muestra estado de los servicios"
        echo "  logs [srv]      - Muestra logs (Ctrl+C para salir)"
        echo "  connect [srv]   - Conecta a la sesión tmux"
        echo ""
        echo -e "${GREEN}Servicios:${NC}"
        echo "  backend         - FastAPI (sat-analysis)"
        echo "  frontend        - Next.js (chatbot)"
        echo ""
        echo -e "${GREEN}Ejemplos:${NC}"
        echo "  devctl start"
        echo "  devctl restart backend"
        echo "  devctl logs frontend"
        exit 1
        ;;
esac
