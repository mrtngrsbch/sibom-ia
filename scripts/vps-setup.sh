#!/usr/bin/env bash
# =============================================================================
# vps-setup.sh — Configuración inicial del VPS Hostinger KVM 2
# Ejecutar UNA SOLA VEZ como root en el servidor
# Uso: bash vps-setup.sh
# =============================================================================
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✓] $*${NC}"; }
warn() { echo -e "${YELLOW}[!] $*${NC}"; }
fail() { echo -e "${RED}[✗] $*${NC}"; exit 1; }

[[ $EUID -ne 0 ]] && fail "Ejecutar como root: sudo bash vps-setup.sh"

# ── 1. Actualizar sistema ─────────────────────────────────────────────────────
log "Actualizando sistema..."
apt-get update -qq && apt-get upgrade -y -qq

# ── 2. Instalar dependencias base ─────────────────────────────────────────────
log "Instalando dependencias base..."
apt-get install -y -qq \
  curl wget git rsync unzip \
  ca-certificates gnupg lsb-release \
  ufw fail2ban

# ── 3. Instalar Docker ────────────────────────────────────────────────────────
if command -v docker &>/dev/null; then
  warn "Docker ya instalado: $(docker --version)"
else
  log "Instalando Docker..."
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg

  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    | tee /etc/apt/sources.list.d/docker.list > /dev/null

  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin
  systemctl enable --now docker
  log "Docker $(docker --version) instalado"
fi

# ── 4. Crear usuario deploy (no-root) ─────────────────────────────────────────
if ! id deploy &>/dev/null; then
  log "Creando usuario 'deploy'..."
  useradd -m -s /bin/bash deploy
  usermod -aG docker deploy
  log "Usuario 'deploy' creado y añadido al grupo docker"
else
  warn "Usuario 'deploy' ya existe"
  usermod -aG docker deploy
fi

# ── 5. Configurar directorio de la app ────────────────────────────────────────
APP_DIR=/opt/mangrullo
log "Configurando directorio $APP_DIR..."
mkdir -p "$APP_DIR"
chown deploy:deploy "$APP_DIR"

# ── 6. Firewall básico ────────────────────────────────────────────────────────
log "Configurando UFW..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp    # HTTP (Cloudflare → nginx)
ufw allow 443/tcp   # HTTPS (opcional, Cloudflare termina TLS)
ufw --force enable
log "Firewall activo"

# ── 7. Resumen ────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  VPS configurado correctamente${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo ""
echo "Próximos pasos (desde tu máquina local):"
echo "  1. Copia tu clave SSH al VPS:"
echo "     ssh-copy-id deploy@<IP_VPS>"
echo "  2. Ejecuta el deploy:"
echo "     bash scripts/deploy.sh <IP_VPS>"
echo ""
