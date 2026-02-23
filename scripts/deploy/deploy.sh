#!/usr/bin/env bash
# =============================================================================
# deploy.sh — Pull latest code, rebuild, and restart the platform
#
# Usage:
#   ssh user@VM_IP 'cd /opt/indigitall-analytics && bash scripts/deploy/deploy.sh'
# =============================================================================

set -euo pipefail

APP_DIR="/opt/indigitall-analytics"
cd "$APP_DIR"

echo "=============================================="
echo " inDigitall BI Platform — Deploy"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="

# --- Pull latest code ---
echo "[1/4] Pulling latest code..."
git pull --ff-only

# --- Rebuild containers ---
echo "[2/4] Building containers..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache app

# --- Restart services ---
echo "[3/4] Restarting services..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# --- Run migrations (create new tables if any) ---
echo "[4/4] Running migrations..."
docker compose exec -T app python -c "from app.models.database import create_tables; create_tables()"

# --- Health check ---
echo ""
echo "[INFO] Waiting for health check..."
sleep 5
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8050/health || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    echo "[OK] Platform is healthy (HTTP $HTTP_STATUS)"
else
    echo "[WARN] Health check returned HTTP $HTTP_STATUS"
    echo "       Check logs: docker compose logs app --tail 50"
fi

echo ""
echo "=============================================="
echo " Deploy complete!"
echo "=============================================="
echo ""
docker compose ps
