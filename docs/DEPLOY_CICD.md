# CI/CD — Deploy Automático con GitHub Actions

## Resumen de Cambios

Se implementó un pipeline de **CI/CD automático** usando GitHub Actions que despliega la plataforma en la VM de GCP cada vez que se hace push a `main`.

### Archivos creados/modificados

| Archivo | Acción | Descripción |
|---|---|---|
| `.github/workflows/deploy.yml` | Creado | Workflow de GitHub Actions |
| `scripts/deploy/deploy.sh` | Modificado | Nuevo paso 5/5: ETL pipeline + deploy log |
| `scripts/deploy/.env.production` | Modificado | Variables de Indigitall API actualizadas |

---

## Flujo de Deploy

```
Tu PC (git push origin main)
    │
    ▼
GitHub Actions (detecta push a main)
    │  Se conecta por SSH a la VM de GCP
    │  Usa: appleboy/ssh-action@v1
    ▼
GCP VM (/opt/indigitall-analytics)
    │  1. git pull --ff-only
    │  2. docker compose build --no-cache app
    │  3. docker compose up -d
    │  4. Migraciones (create_tables)
    │  5. Health check (localhost:8050/health)
    │  6. ETL pipeline (transform_bridge.py)
    │  7. Log de deploy (deploy.log)
    ▼
App actualizada en:
    https://analytics.abstractstudio.co
    https://n8n-indigitall.abstractstudio.co
    https://studio-indigitall.abstractstudio.co
```

---

## Configuración Requerida

### 1. Generar SSH Key en la VM

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions_deploy -N ""
cat ~/.ssh/github_actions_deploy.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/github_actions_deploy   # copiar la clave privada
```

### 2. Configurar GitHub Secrets

En el repositorio → **Settings** → **Secrets and variables** → **Actions**, crear:

| Secret | Valor |
|---|---|
| `GCP_SSH_PRIVATE_KEY` | Contenido completo de `~/.ssh/github_actions_deploy` (clave privada) |
| `GCP_VM_HOST` | IP pública de la VM de GCP |
| `GCP_VM_USER` | Usuario SSH en la VM (ej: `henry`) |

### 3. Verificar .env en la VM

Asegurarse de que `/opt/indigitall-analytics/.env` tenga las variables de Indigitall API:

```env
INDIGITALL_API_BASE_URL=https://am1.api.indigitall.com
INDIGITALL_SERVER_KEY=<tu-server-key>
INDIGITALL_APP_TOKEN=<tu-app-token>
```

---

## Triggers del Workflow

| Trigger | Descripción |
|---|---|
| `push` a `main` | Deploy automático en cada push |
| `workflow_dispatch` | Deploy manual desde GitHub UI (botón "Run workflow") |

---

## Verificación

1. Hacer push a `main`
2. Ir a GitHub → **Actions** → verificar que el job "Deploy" se ejecuta correctamente
3. Verificar `https://analytics.abstractstudio.co/health` → `{"status": "ok"}`
4. Probar deploy manual: GitHub → Actions → "Deploy to GCP VM" → "Run workflow"

---

## Infraestructura

- **VM**: `trax-report-automation` (GCP, zona `southamerica-east1-a`)
- **Reverse Proxy**: Caddy (TLS automático con Let's Encrypt)
- **Contenedores**: Docker Compose (`docker-compose.yml` + `docker-compose.prod.yml`)
- **Timeout del workflow**: 5 minutos (4 min para el script SSH)
