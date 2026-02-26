# Como Funciona el Deploy — inDigitall BI Platform

## Resumen en una frase

Al hacer `git push` a la rama `main` del repo de Henry (`henrysaenz-rocket`), GitHub Actions automaticamente se conecta por SSH a la VM de GCP y actualiza la aplicacion. Todo el proceso toma ~2 minutos sin intervencion manual.

---

## Los Dos Repositorios

El proyecto tiene **dos repos en GitHub** que estan sincronizados:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  henrysaenz-rocket/indigitall-bi-plataform  ← ORIGIN        │
│  (Fork de Henry — donde se hace push)                       │
│  ✅ Tiene GitHub Actions configurado                         │
│  ✅ Tiene los Secrets para SSH                               │
│                                                             │
│          ↕  sincronizados (git push upstream/origin)         │
│                                                             │
│  edelae/indigitall-bi-plataform  ← UPSTREAM                  │
│  (Repo original de Ernesto)                                  │
│  Se mantiene actualizado al hacer push a upstream            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### En tu maquina local (tu PC), los remotes estan asi:

```
origin    → https://github.com/henrysaenz-rocket/indigitall-bi-plataform.git
upstream  → https://github.com/edelae/indigitall-bi-plataform.git
```

### Cual repo dispara el deploy?

**Solo `origin` (henrysaenz-rocket)**. El workflow de GitHub Actions esta en este repo. Si alguien hace push directo al repo de Ernesto (`edelae`), NO se dispara deploy automatico.

---

## Flujo Completo Paso a Paso

### Paso 1: Tu haces cambios en tu PC

```
Tu PC (Windows)
  └── C:\Users\henry\...\indigitall-bi-plataform\
      ├── app/          ← Codigo de la app Dash
      ├── scripts/      ← Extractores, pipeline, deploy
      ├── dbt/          ← Modelos de datos
      ├── n8n/          ← Workflows de automatizacion
      └── .github/workflows/deploy.yml  ← El workflow de CI/CD
```

Haces tus cambios, luego:

```bash
git add <archivos>
git commit -m "Descripcion del cambio"
git push origin main        # ← ESTO dispara el deploy automatico
git push upstream main      # ← Opcional: sincroniza el repo de Ernesto
```

### Paso 2: GitHub Actions detecta el push

En cuanto GitHub recibe el push a `main` en `henrysaenz-rocket/indigitall-bi-plataform`, activa el workflow `.github/workflows/deploy.yml`:

```
┌─────────────────────────────────────────────────────────────┐
│  GitHub Actions                                              │
│                                                             │
│  Trigger: push a main  (o workflow_dispatch manual)          │
│                                                             │
│  1. Usa appleboy/ssh-action@v1                               │
│  2. Se conecta por SSH a la VM de GCP                        │
│     - Host: ${{ secrets.GCP_VM_HOST }}   → 34.151.199.149    │
│     - User: ${{ secrets.GCP_VM_USER }}   → hsaenz            │
│     - Key:  ${{ secrets.GCP_SSH_PRIVATE_KEY }}               │
│  3. Ejecuta: cd /opt/indigitall-analytics                    │
│              bash scripts/deploy/deploy.sh                   │
│                                                             │
│  Timeout: 5 minutos                                          │
└─────────────────────────────────────────────────────────────┘
```

### Paso 3: deploy.sh se ejecuta en la VM

El script `scripts/deploy/deploy.sh` hace 5 pasos dentro de la VM de GCP:

```
VM de GCP (indigitall-analytics)
    /opt/indigitall-analytics/

    [1/5] git pull --ff-only
          └── Trae el codigo mas reciente de GitHub

    [2/5] docker compose build --no-cache app
          └── Reconstruye SOLO el contenedor de la app Dash
              (PostgreSQL, n8n, Supabase Studio NO se tocan)

    [3/5] docker compose up -d
          └── Reinicia los servicios
              (los que no cambiaron se mantienen corriendo)

    [4/5] python create_tables()
          └── Crea tablas nuevas si se agregaron modelos
              (idempotente — no borra datos existentes)

    [5/5] python transform_bridge.py
          └── Re-procesa raw.* → public.* (ETL pipeline)
              (idempotente — UPSERT, seguro de re-ejecutar)

    Health check: curl localhost:8050/health
          └── Verifica que la app responde correctamente

    Log: deploy.log
          └── Registra fecha/hora y resultado del deploy
```

### Paso 4: La app esta actualizada

```
Internet → Caddy (TLS automatico)
               ↓
        ┌──────┴──────────────────────────────────────┐
        │                                             │
        │  analytics.abstractstudio.co → :8050 (Dash) │
        │  n8n-indigitall.abstractstudio.co → :5678   │
        │  studio-indigitall.abstractstudio.co → :3000│
        │                                             │
        └─────────────────────────────────────────────┘
```

---

## Diagrama Completo del Flujo

```
    TU PC                    GITHUB                     GCP VM
    ─────                    ──────                     ──────

  git commit          push a main
  git push origin ──────────────►  henrysaenz-rocket/
       │                           indigitall-bi-plataform
       │                                │
       │                    GitHub Actions detecta push
       │                                │
       │                    ┌───────────▼───────────┐
       │                    │ deploy.yml             │
       │                    │                       │
       │                    │ 1. SSH connect         │
       │                    │ 2. Run deploy.sh       │
       │                    └───────────┬───────────┘
       │                                │
       │                         SSH    │
       │                                ▼
       │                    ┌───────────────────────┐
       │                    │ 34.151.199.149        │
       │                    │ /opt/indigitall-...   │
       │                    │                       │
       │                    │ git pull              │
       │                    │ docker build          │
       │                    │ docker up             │
       │                    │ create_tables()       │
       │                    │ transform_bridge.py   │
       │                    │ health check          │
       │                    └───────────────────────┘
       │                                │
       │                                ▼
       │                    App actualizada en:
       │                    analytics.abstractstudio.co
       │
  git push upstream ────►  edelae/indigitall-bi-plataform
  (sincronizar)            (repo de Ernesto — NO dispara deploy)
```

---

## Los 3 Metodos de Deploy

### Metodo 1: Automatico (push a main) — RECOMENDADO

```bash
# Desde tu PC
git add .
git commit -m "Cambio X"
git push origin main
# → GitHub Actions hace todo automaticamente (~2 min)
```

**Verificar**: Ir a https://github.com/henrysaenz-rocket/indigitall-bi-plataform/actions

### Metodo 2: Manual desde GitHub (sin terminal)

1. Ir a: https://github.com/henrysaenz-rocket/indigitall-bi-plataform/actions
2. Click en **"Deploy to GCP VM"** (panel izquierdo)
3. Click en **"Run workflow"** → **"Run workflow"**
4. Esperar ~2 minutos

Esto funciona desde **cualquier dispositivo con navegador** (PC, tablet, celular).

### Metodo 3: SSH directo a la VM

```bash
# Opcion A: Entrar a la VM y ejecutar deploy
gcloud compute ssh indigitall-analytics \
  --project=trax-report-automation \
  --zone=southamerica-east1-a

# Dentro de la VM:
cd /opt/indigitall-analytics
bash scripts/deploy/deploy.sh

# Opcion B: Sin entrar (un solo comando)
gcloud compute ssh indigitall-analytics \
  --project=trax-report-automation \
  --zone=southamerica-east1-a \
  --command="cd /opt/indigitall-analytics && bash scripts/deploy/deploy.sh"
```

---

## Que Pasa con Cada Repo

### henrysaenz-rocket (origin) — Repo principal de trabajo

| Aspecto | Detalle |
|---|---|
| **Rol** | Fork de Henry — se hace push aqui |
| **Deploy automatico** | SI — GitHub Actions en push a `main` |
| **GitHub Secrets** | GCP_SSH_PRIVATE_KEY, GCP_VM_HOST, GCP_VM_USER |
| **Cuando usar** | Siempre — es el repo principal |

### edelae (upstream) — Repo original de Ernesto

| Aspecto | Detalle |
|---|---|
| **Rol** | Repo original — se sincroniza manualmente |
| **Deploy automatico** | NO — no tiene GitHub Actions |
| **GitHub Secrets** | No tiene |
| **Cuando usar** | Para compartir codigo con Ernesto |

### Como sincronizar los dos repos

```bash
# 1. Push normal (tu trabajo → tu repo → deploy automatico)
git push origin main

# 2. Sincronizar con Ernesto (push al repo de el)
git push upstream main

# 3. Traer cambios de Ernesto (si el hizo cambios directos)
git fetch upstream
git merge upstream/main
git push origin main    # → esto dispara deploy automatico
```

---

## Que se Despliega (Docker Compose)

La VM corre 7 servicios con Docker Compose:

```
┌─────────────────────────────────────────────────────────┐
│  Docker Compose en la VM                                │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ PostgreSQL│  │   Dash   │  │   n8n    │              │
│  │ (Supabase)│  │   App    │  │(workflow)│              │
│  │  :5432   │  │  :8050   │  │  :5678   │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ PostgREST│  │  Studio  │  │   Kong   │              │
│  │ (API)    │  │(DB admin)│  │(gateway) │              │
│  │  :3001   │  │  :3000   │  │  :8000   │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│                                                         │
│  ┌──────────┐                                           │
│  │  Supabase│                                           │
│  │   Meta   │                                           │
│  └──────────┘                                           │
└─────────────────────────────────────────────────────────┘
          │
    Caddy (Reverse Proxy + TLS automatico)
          │
    ┌─────┴─────────────────────────────────────┐
    │ analytics.abstractstudio.co    → :8050     │
    │ n8n-indigitall.abstractstudio.co → :5678   │
    │ studio-indigitall.abstractstudio.co → :3000│
    └───────────────────────────────────────────┘
```

**Al hacer deploy, SOLO se reconstruye el contenedor `app` (Dash).** PostgreSQL, n8n, Studio, Kong, etc. **no se tocan** — mantienen su estado y datos.

---

## GitHub Secrets Configurados

| Secret | Valor | Donde |
|---|---|---|
| `GCP_SSH_PRIVATE_KEY` | Clave privada SSH ed25519 | Solo en henrysaenz-rocket |
| `GCP_VM_HOST` | `34.151.199.149` | Solo en henrysaenz-rocket |
| `GCP_VM_USER` | `hsaenz` | Solo en henrysaenz-rocket |

Estos secrets permiten que GitHub Actions se conecte por SSH a la VM sin intervencion.

---

## Que Pasa si el Deploy Falla

### Ver los logs de GitHub Actions

1. Ir a https://github.com/henrysaenz-rocket/indigitall-bi-plataform/actions
2. Click en el workflow fallido
3. Click en "Deploy" → ver logs detallados

### Errores comunes

| Error | Causa | Solucion |
|---|---|---|
| `Permission denied (publickey)` | SSH key no esta en la VM | Ernesto debe agregar la key (ver SETUP_SSH_DEPLOY.md) |
| `Connection timed out` | VM apagada o sin red | Revisar VM en consola GCP |
| `docker compose: command not found` | Docker no instalado | Ejecutar scripts/deploy/setup_vm.sh |
| Health check `HTTP 000` | App no arranco | `docker compose logs app --tail 50` |
| `Already up to date` en git pull | No hay cambios nuevos | Normal — el deploy sigue sin errores |

### Rollback (volver a version anterior)

```bash
# En tu PC
git revert HEAD
git push origin main
# → GitHub Actions despliega la version anterior automaticamente
```

---

## Pipeline de Datos (Automatico Post-Deploy)

Despues de cada deploy, el script ejecuta `transform_bridge.py` que procesa los datos:

```
Indigitall API
    ↓ (extractores cada 6h via n8n)
raw.* (JSONB crudo)
    ↓ (transform_bridge.py — ejecuta en cada deploy)
public.* (tablas estructuradas)
    ↓ (dbt — staging → marts)
Dashboard Dash (analytics.abstractstudio.co)
```

Adicionalmente, n8n ejecuta automaticamente:
- **Cada 6 horas**: ETL completo (extraccion API + transform + dbt)
- **Cada 1 hora**: Solo transform (re-procesa datos raw existentes)

---

## Infraestructura

| Componente | Detalle |
|---|---|
| **VM** | `indigitall-analytics` (GCP Compute Engine) |
| **IP** | `34.151.199.149` |
| **Proyecto GCP** | `trax-report-automation` |
| **Zona** | `southamerica-east1-a` |
| **OS** | Ubuntu (con Docker + Caddy) |
| **Reverse Proxy** | Caddy (TLS automatico con Let's Encrypt) |
| **CI/CD** | GitHub Actions (`deploy.yml`) |
| **Contenedores** | Docker Compose (7 servicios) |
| **Base de datos** | PostgreSQL 15 (Supabase self-hosted) |

---

## Resumen Visual

```
┌───────────────────────────────────────────────────────────────────┐
│                                                                   │
│  1. git push origin main                                          │
│     └── Desde tu PC, tablet, o cualquier dispositivo con Git      │
│                                                                   │
│  2. GitHub Actions (automatico)                                   │
│     └── Se conecta por SSH a la VM de GCP                         │
│     └── Ejecuta deploy.sh                                         │
│                                                                   │
│  3. deploy.sh (en la VM)                                          │
│     └── git pull                                                  │
│     └── docker build (solo app)                                   │
│     └── docker up -d                                              │
│     └── create_tables()                                           │
│     └── transform_bridge.py                                       │
│     └── health check                                              │
│                                                                   │
│  4. App actualizada                                               │
│     └── https://analytics.abstractstudio.co                       │
│     └── https://n8n-indigitall.abstractstudio.co                  │
│     └── https://studio-indigitall.abstractstudio.co               │
│                                                                   │
│  Tiempo total: ~2 minutos                                         │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```
