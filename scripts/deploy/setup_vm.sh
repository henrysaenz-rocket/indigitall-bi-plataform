#!/usr/bin/env bash
# =============================================================================
# setup_vm.sh — Bootstrap a fresh Ubuntu 22.04 VM for inDigitall BI Platform
#
# Usage (run as root on a fresh GCP VM):
#   curl -sSL https://raw.githubusercontent.com/.../setup_vm.sh | bash
#   — or —
#   scp scripts/deploy/setup_vm.sh user@VM_IP:/tmp/ && ssh user@VM_IP 'sudo bash /tmp/setup_vm.sh'
# =============================================================================

set -euo pipefail

echo "=============================================="
echo " inDigitall BI Platform — VM Setup"
echo "=============================================="

# --- System updates ---
echo "[1/5] Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    unzip \
    htop \
    jq

# --- Docker ---
echo "[2/5] Installing Docker..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    # Allow current user to run docker without sudo
    usermod -aG docker "${SUDO_USER:-$(whoami)}" 2>/dev/null || true
fi
docker --version

# --- Docker Compose (v2 plugin) ---
echo "[3/5] Installing Docker Compose..."
if ! docker compose version &>/dev/null; then
    DOCKER_CONFIG=${DOCKER_CONFIG:-/usr/local/lib/docker}
    mkdir -p "$DOCKER_CONFIG/cli-plugins"
    curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
        -o "$DOCKER_CONFIG/cli-plugins/docker-compose"
    chmod +x "$DOCKER_CONFIG/cli-plugins/docker-compose"
fi
docker compose version

# --- Caddy (reverse proxy with auto-SSL) ---
echo "[4/5] Installing Caddy..."
if ! command -v caddy &>/dev/null; then
    apt-get install -y -qq debian-keyring debian-archive-keyring apt-transport-https
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | \
        gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | \
        tee /etc/apt/sources.list.d/caddy-stable.list
    apt-get update -qq
    apt-get install -y -qq caddy
fi
caddy version

# --- Create app directory ---
echo "[5/5] Setting up application directory..."
APP_DIR="/opt/indigitall-analytics"
mkdir -p "$APP_DIR"
chown "${SUDO_USER:-$(whoami)}:${SUDO_USER:-$(whoami)}" "$APP_DIR" 2>/dev/null || true

# --- Firewall (ufw) ---
echo "[INFO] Configuring firewall..."
if command -v ufw &>/dev/null; then
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
fi

# --- Swap (2GB for e2-standard-2) ---
echo "[INFO] Configuring swap..."
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo ""
echo "=============================================="
echo " Setup complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "  1. Clone the repo to $APP_DIR"
echo "  2. Copy .env.production to $APP_DIR/.env"
echo "  3. Copy Caddyfile to /etc/caddy/Caddyfile"
echo "  4. Run: cd $APP_DIR && docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d"
echo "  5. Seed data: docker compose exec app python scripts/seed_data.py"
echo "  6. Start Caddy: systemctl restart caddy"
echo ""
