#!/bin/bash
# Script de desarrollo local - Ejecuta servicios nativos (sin Docker)
# Uso: ./scripts/dev.sh

set -e

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Iniciando servicios en modo desarrollo...${NC}"

# Variables para rastrear qué servicios inició este script
BACKEND_STARTED_BY_SCRIPT=false
FRONTEND_STARTED_BY_SCRIPT=false

# Función para limpiar procesos al salir
cleanup() {
    echo -e "\n${YELLOW}🛑 Deteniendo servicios...${NC}"
    if [ "$BACKEND_STARTED_BY_SCRIPT" = true ] && [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Backend detenido${NC}"
    else
        echo -e "${BLUE}ℹ️  Backend iniciado externamente, no se detiene${NC}"
    fi

    if [ "$FRONTEND_STARTED_BY_SCRIPT" = true ] && [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Frontend detenido${NC}"
    else
        echo -e "${BLUE}ℹ️  Frontend iniciado externamente, no se detiene${NC}"
    fi

    echo -e "${GREEN}✅ Servicios detenidos${NC}"
    exit 0
}

trap cleanup INT TERM

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: Ejecutar desde la raíz del proyecto${NC}"
    exit 1
fi

# Crear directorio de logs si no existe
if [ ! -d "logs" ]; then
    mkdir -p logs
fi

# Verificar dependencias de Python
echo -e "${BLUE}📦 Verificando dependencias de Python...${NC}"
if [ ! -d "sat-analysis/venv" ]; then
    echo -e "${YELLOW}Creando virtualenv para sat-analysis...${NC}"
    cd sat-analysis
    python3 -m venv venv
    source venv/bin/activate
    pip install -q -r requirements.txt
    cd ..
fi

# Verificar dependencias de Node
echo -e "${BLUE}📦 Verificando dependencias de Node...${NC}"
if [ ! -d "chatbot/node_modules" ]; then
    echo -e "${YELLOW}Instalando dependencias de chatbot...${NC}"
    cd chatbot
    npm install
    cd ..
fi

# Función para verificar si un puerto está en uso
port_in_use() {
    lsof -ti :$1 >/dev/null 2>&1
}

# Función para obtener el PID que usa un puerto
get_pid_on_port() {
    lsof -ti :$1 2>/dev/null | head -1
}

# Verificar si el puerto 8001 ya está en uso
BACKEND_PID=""
if port_in_use 8001; then
    EXISTING_PID=$(get_pid_on_port 8001)
    EXISTING_CMD=$(ps -p $EXISTING_PID -o command= 2>/dev/null)

    if [[ $EXISTING_CMD == *"uvicorn"* ]] || [[ $EXISTING_CMD == *"api.main"* ]]; then
        echo -e "${GREEN}✅ Backend ya corriendo (PID: $EXISTING_PID)${NC}"
        BACKEND_PID=$EXISTING_PID
    else
        echo -e "${RED}❌ Error: El puerto 8001 está en uso por otro proceso (PID: $EXISTING_PID)${NC}"
        echo -e "   Comando: $EXISTING_CMD"
        echo -e "${YELLOW}   Detén el proceso con: kill $EXISTING_PID${NC}"
        exit 1
    fi
else
    # Iniciar backend FastAPI
    echo -e "${BLUE}🔧 Backend: Iniciando FastAPI con auto-reload...${NC}"
    cd sat-analysis
    source venv/bin/activate
    python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8001 > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    BACKEND_STARTED_BY_SCRIPT=true
    cd ..

    # Esperar a que el backend inicie
    sleep 3

    # Verificar que el backend esté corriendo
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}❌ Error: El backend no inició correctamente${NC}"
        cat logs/backend.log
        exit 1
    fi
fi

# Verificar si el puerto 3000 ya está en uso
FRONTEND_PID=""
if port_in_use 3000; then
    EXISTING_PID=$(get_pid_on_port 3000)
    EXISTING_CMD=$(ps -p $EXISTING_PID -o command= 2>/dev/null)

    if [[ $EXISTING_CMD == *"next"* ]] || [[ $EXISTING_CMD == *"node"* ]] || [[ $EXISTING_CMD == *"bun"* ]]; then
        echo -e "${GREEN}✅ Frontend ya corriendo (PID: $EXISTING_PID)${NC}"
        FRONTEND_PID=$EXISTING_PID
    else
        echo -e "${RED}❌ Error: El puerto 3000 está en uso por otro proceso (PID: $EXISTING_PID)${NC}"
        echo -e "   Comando: $EXISTING_CMD"
        echo -e "${YELLOW}   Detén el proceso con: kill $EXISTING_PID${NC}"
        cleanup
        exit 1
    fi
else
    # Iniciar frontend Next.js
    echo -e "${BLUE}⚛️  Frontend: Iniciando Next.js con auto-reload...${NC}"
    cd chatbot
    npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    FRONTEND_STARTED_BY_SCRIPT=true
    cd ..

    # Esperar a que el frontend inicie
    sleep 3

    # Verificar que el frontend esté corriendo
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}❌ Error: El frontend no inició correctamente${NC}"
        cat logs/frontend.log
        cleanup
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}✅ Servicios iniciados correctamente!${NC}"
echo ""
echo -e "${BLUE}Frontend:${NC}    http://localhost:3000"
echo -e "${BLUE}Backend:${NC}     http://localhost:8001"
echo -e "${BLUE}API Docs:${NC}    http://localhost:8001/docs"
echo -e "${BLUE}Satélite:${NC}    http://localhost:3000/satelite"
echo ""
echo -e "${YELLOW}Presiona Ctrl+C para detener todos los servicios${NC}"
echo ""

# Mantener el script corriendo
wait
