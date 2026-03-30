#!/usr/bin/env bash
# =============================================================================
# deploy.sh — Deploy de Mangrullo en Hostinger KVM 2
# Uso: bash scripts/deploy.sh <IP_VPS> [usuario]
#
# Ejemplos:
#   bash scripts/deploy.sh 192.168.1.100
#   bash scripts/deploy.sh 192.168.1.100 deploy
# =============================================================================
set -euo pipefail

# ── Parámetros ────────────────────────────────────────────────────────────────
VPS_IP="${1:-}"
VPS_USER="${2:-deploy}"
APP_DIR="/opt/mangrullo"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✓] $*${NC}"; }
warn() { echo -e "${YELLOW}[!] $*${NC}"; }
fail() { echo -e "${RED}[✗] $*${NC}"; exit 1; }
step() { echo -e "\n${BOLD}── $* ──${NC}"; }

# ── Validaciones locales ──────────────────────────────────────────────────────
[[ -z "$VPS_IP" ]] && fail "Uso: bash scripts/deploy.sh <IP_VPS> [usuario]"

[[ ! -f "$REPO_ROOT/.env" ]] && fail \
  "Archivo .env no encontrado en $REPO_ROOT\n  Copia .env.production.example → .env y completa los valores"

# Verificar archivos de índice RAG (requeridos por docker-compose)
INDEXES_DIR="$REPO_ROOT/python-cli/data/indexes"
for f in boletines_index.json normativas_index_minimal.json normativas_index.json; do
  [[ ! -f "$INDEXES_DIR/$f" ]] && fail "Archivo de índice faltante: $INDEXES_DIR/$f"
done
log "Archivos de índice RAG verificados"

SSH_TARGET="$VPS_USER@$VPS_IP"

# ── Verificar conectividad SSH ────────────────────────────────────────────────
step "Verificando conexión SSH a $SSH_TARGET"
ssh -o ConnectTimeout=10 -o BatchMode=yes "$SSH_TARGET" "echo 'SSH OK'" \
  || fail "No se puede conectar a $SSH_TARGET\n  Verifica que tu clave SSH esté copiada: ssh-copy-id $SSH_TARGET"
log "Conexión SSH exitosa"

# ── Preparar directorios en el VPS ───────────────────────────────────────────
step "Preparando estructura de directorios en VPS"
ssh "$SSH_TARGET" "mkdir -p $APP_DIR/python-cli/data/indexes"
log "Directorios creados"

# ── Sincronizar código fuente (sin archivos ignorados) ───────────────────────
step "Sincronizando código fuente"
rsync -avz --progress \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='.next' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.venv' \
  --exclude='venv' \
  --exclude='python-cli/data/' \
  --exclude='python-cli/boletines/' \
  --exclude='.env' \
  --exclude='.env.local' \
  --exclude='*.log' \
  --exclude='sat-analysis/web_output/' \
  --filter=':- .gitignore' \
  "$REPO_ROOT/" "$SSH_TARGET:$APP_DIR/"
log "Código fuente sincronizado"

# ── Sincronizar archivos de índice RAG (~27MB) ────────────────────────────────
step "Transfiriendo índices RAG (~27MB)"
rsync -avz --progress \
  "$INDEXES_DIR/boletines_index.json" \
  "$INDEXES_DIR/normativas_index_minimal.json" \
  "$INDEXES_DIR/normativas_index.json" \
  "$SSH_TARGET:$APP_DIR/python-cli/data/indexes/"
log "Índices RAG transferidos"

# ── Transferir archivo .env ───────────────────────────────────────────────────
step "Transfiriendo .env (secretos)"
rsync -avz "$REPO_ROOT/.env" "$SSH_TARGET:$APP_DIR/.env"
log ".env transferido"

# ── Build y arranque con Docker Compose ──────────────────────────────────────
step "Construyendo y arrancando servicios con Docker Compose"
ssh "$SSH_TARGET" bash <<EOF
  set -euo pipefail
  cd $APP_DIR

  echo "[→] Deteniendo contenedores previos (si existen)..."
  docker compose down --remove-orphans 2>/dev/null || true

  echo "[→] Construyendo imágenes..."
  docker compose build --no-cache

  echo "[→] Arrancando servicios en background..."
  docker compose up -d

  echo "[→] Estado de los servicios:"
  docker compose ps
EOF

log "Servicios arrancados"

# ── Verificar health del chatbot ──────────────────────────────────────────────
step "Verificando health del chatbot"
echo "Esperando que los servicios estén listos (60s)..."
sleep 60

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  --max-time 10 "http://$VPS_IP" 2>/dev/null || echo "000")

if [[ "$HTTP_STATUS" == "200" ]]; then
  log "Chatbot respondiendo en http://$VPS_IP (HTTP $HTTP_STATUS)"
else
  warn "HTTP $HTTP_STATUS — puede necesitar más tiempo para iniciar"
  warn "Verificar manualmente: ssh $SSH_TARGET 'cd $APP_DIR && docker compose ps && docker compose logs --tail=50'"
fi

# ── Resumen final ─────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  Deploy completado${NC}"
echo -e "${GREEN}${BOLD}════════════════════════════════════════════════${NC}"
echo ""
echo "  URL:          http://$VPS_IP"
echo "  SSH logs:     ssh $SSH_TARGET 'cd $APP_DIR && docker compose logs -f'"
echo "  SSH status:   ssh $SSH_TARGET 'cd $APP_DIR && docker compose ps'"
echo ""
echo "  Configurar DNS Cloudflare:"
echo "    mangrullo.microagencia.com → A → $VPS_IP"
echo ""
