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

# Verificar si Overmind ya está corriendo
if overmind status >/dev/null 2>&1; then
    echo ""
    echo -e "${GREEN}✅ Overmind ya está corriendo${NC}"
    echo ""
    echo -e "${CYAN}   Conectando a la sesión existente...${NC}"
    echo ""
    exec overmind connect
fi

# Verificar si los puertos están en uso por procesos externos
BACKEND_EXTERNAL_PID=""
FRONTEND_EXTERNAL_PID=""
BACKEND_RUNNING=false
FRONTEND_RUNNING=false

if port_in_use 8001; then
    BACKEND_PID=$(get_pid_on_port 8001)
    # Verificar si es un proceso de Overmind
    if ps -p $BACKEND_PID -o command= 2>/dev/null | grep -q "overmind"; then
        BACKEND_RUNNING=true
    else
        BACKEND_EXTERNAL_PID=$BACKEND_PID
    fi
fi

if port_in_use 3000; then
    FRONTEND_PID=$(get_pid_on_port 3000)
    # Verificar si es un proceso de Overmind
    if ps -p $FRONTEND_PID -o command= 2>/dev/null | grep -q "overmind"; then
        FRONTEND_RUNNING=true
    else
        FRONTEND_EXTERNAL_PID=$FRONTEND_PID
    fi
fi

# Si hay servicios externos corriendo, preguntar
if [ ! -z "$BACKEND_EXTERNAL_PID" ] || [ ! -z "$FRONTEND_EXTERNAL_PID" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Servicios detectados corriendo externamente:${NC}"
    echo ""

    if [ ! -z "$BACKEND_EXTERNAL_PID" ]; then
        echo -e "   Backend:  ${RED}Corriendo (PID: $BACKEND_EXTERNAL_PID)${NC}"
    fi

    if [ ! -z "$FRONTEND_EXTERNAL_PID" ]; then
        echo -e "   Frontend: ${RED}Corriendo (PID: $FRONTEND_EXTERNAL_PID)${NC}"
    fi

    echo ""
    echo -e "${YELLOW}Overmind necesita detener estos servicios primero.${NC}"
    echo ""
    echo -e "${CYAN}Opciones:${NC}"
    echo -e "   ${GREEN}1${NC} - Detener servicios externos y usar Overmind"
    echo -e "   ${GREEN}2${NC} - Cancelar y mantener servicios actuales"
    echo ""
    echo -n "   Selecciona (1/2): "
    read -r choice

    if [ "$choice" != "1" ]; then
        echo ""
        echo -e "${YELLOW}Cancelado. Servicios externos mantienen ejecución.${NC}"
        echo ""
        echo -e "${CYAN}Para usar Overmind, detén primero:${NC}"
        if [ ! -z "$BACKEND_EXTERNAL_PID" ]; then
            echo -e "   kill $BACKEND_EXTERNAL_PID  # Backend"
        fi
        if [ ! -z "$FRONTEND_EXTERNAL_PID" ]; then
            echo -e "   kill $FRONTEND_EXTERNAL_PID  # Frontend"
        fi
        exit 0
    fi

    # Detener servicios externos
    echo ""
    echo -e "${YELLOW}Deteniendo servicios externos...${NC}"

    if [ ! -z "$BACKEND_EXTERNAL_PID" ]; then
        kill $BACKEND_EXTERNAL_PID 2>/dev/null || true
        echo -e "${GREEN}   ✅ Backend detenido${NC}"
    fi

    if [ ! -z "$FRONTEND_EXTERNAL_PID" ]; then
        kill $FRONTEND_EXTERNAL_PID 2>/dev/null || true
        # Esperar un poco para que libere el puerto
        sleep 1
        if port_in_use 3000; then
            # Intentar con SIGTERM al group
            kill -9 -$FRONTEND_EXTERNAL_PID 2>/dev/null || true
        fi
        echo -e "${GREEN}   ✅ Frontend detenido${NC}"
    fi

    echo ""
fi

# Mostrar estado actual
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  📊 Iniciando Servicios${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}  Backend:  FastAPI (sat-analysis) en puerto 8001${NC}"
echo -e "${CYAN}  Frontend: Next.js (chatbot) en puerto 3000${NC}"
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
echo -e "     ${GREEN}overmind connect backend${NC} - Conectar al panel de backend"
echo ""
echo -e "${YELLOW}  Presiona Ctrl+B luego D para desconectar sin detener${NC}"
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
