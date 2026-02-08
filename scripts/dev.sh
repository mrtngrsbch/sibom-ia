#!/bin/bash
# Script de desarrollo local con Overmind
# Uso: ./scripts/dev.sh

set -e

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
cat <<'EOF'
╔════════════════════════════════════════════════════════════╗
║                                                          ║
║        🚀 SIBOM Dev - Entorno de Desarrollo              ║
║                                                          ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: Ejecutar desde la raíz del proyecto${NC}"
    exit 1
fi

# Crear directorio de logs si no existe
if [ ! -d "logs" ]; then
    mkdir -p logs
fi

# Verificar dependencias
echo -e "${BLUE}📦 Verificando dependencias...${NC}"

# Verificar virtualenv de Python
if [ ! -d "sat-analysis/venv" ]; then
    echo -e "${YELLOW}   Creando virtualenv para sat-analysis...${NC}"
    cd sat-analysis
    python3 -m venv venv
    source venv/bin/activate
    pip install -q -r requirements.txt
    cd ..
fi

# Verificar node_modules
if [ ! -d "chatbot/node_modules" ]; then
    echo -e "${YELLOW}   Instalando dependencias de chatbot...${NC}"
    cd chatbot
    npm install --silent
    cd ..
fi

echo -e "${GREEN}   ✅ Dependencias OK${NC}"

# Verificar Overmind
if ! command -v overmind &> /dev/null; then
    echo ""
    echo -e "${YELLOW}⚠️  Overmind no está instalado.${NC}"
    echo -e "${CYAN}   Para instalar:${NC}"
    echo -e "   ${GREEN}brew install tmux overmind${NC}"
    echo ""
    echo -e "${YELLOW}   Usando modo fallback (scripts individuales)...${NC}"
    echo ""

    # Modo fallback: iniciar servicios manualmente
    exec python3 scripts/dev-tui.py
fi

# Función para verificar si un puerto está en uso
port_in_use() {
    lsof -ti :$1 >/dev/null 2>&1
}

get_pid_on_port() {
    lsof -ti :$1 2>/dev/null | head -1
}

# Mostrar estado actual
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  📊 Estado de Servicios${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Backend
if port_in_use 8001; then
    BACKEND_PID=$(get_pid_on_port 8001)
    echo -e "${GREEN}  ✅${NC} Backend       ${GREEN}Corriendo${NC}      (PID: ${BACKEND_PID})"
else
    echo -e "${YELLOW}  ⏸️  Backend       Detenido${NC}"
fi

# Frontend
if port_in_use 3000; then
    FRONTEND_PID=$(get_pid_on_port 3000)
    echo -e "${GREEN}  ✅${NC} Frontend      ${GREEN}Corriendo${NC}      (PID: ${FRONTEND_PID})"
else
    echo -e "${YELLOW}  ⏸️  Frontend      Detenido${NC}"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🔗 URLs${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "     Frontend:       ${CYAN}http://localhost:3000${NC}"
echo -e "     Backend:        ${CYAN}http://localhost:8001${NC}"
echo -e "     API Docs:       ${CYAN}http://localhost:8001/docs${NC}"
echo -e "     Satélite:       ${CYAN}http://localhost:3000/satelite${NC}"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}  Comandos útiles:${NC}"
echo -e "     ${GREEN}overmind status${NC}         - Ver estado de servicios"
echo -e "     ${GREEN}overmind restart backend${NC} - Reiniciar solo backend"
echo -e "     ${GREEN}overmind logs${NC}           - Ver logs (salir: Ctrl+C)"
echo ""
echo -e "${YELLOW}  Presiona Ctrl+C para detener todos los servicios${NC}"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Función de cleanup
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Deteniendo servicios...${NC}"
    overmind stop
    echo -e "${GREEN}✅ Servicios detenidos${NC}"
    exit 0
}

trap cleanup INT TERM

# Iniciar Overmind
exec overmind start
