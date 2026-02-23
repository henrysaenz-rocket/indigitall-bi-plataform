# inDigitall BI Platform

White-labeled analytics platform for indigitall — Redash-inspired query builder with AI assistant.

## Architecture

- **Frontend:** Plotly Dash + Dash Bootstrap Components
- **Database:** Supabase Self-Hosted (PostgreSQL 15 + PostgREST + RLS)
- **AI Agent:** Claude Sonnet 4.5 (Anthropic) with 13 pre-built functions + SQL fallback
- **Data Pipeline:** n8n (ingestion) + dbt (transformation) + CLI ingestion scripts
- **Auth:** JWT validation from indigitall's shared cookie
- **Deployment:** GCP VM + Docker Compose + Caddy (auto-SSL)

## Quick Start

### 1. Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 2. Kong Configuration

```bash
mkdir -p volumes/kong
# Copy kong.yml (see below)
```

### 3. Run

```bash
docker compose up -d
```

### Services

| Service | URL | Description |
|---------|-----|-------------|
| Dash App | http://localhost:8050 | Analytics platform |
| Supabase Studio | http://localhost:3000 | Database admin |
| n8n | http://localhost:5678 | Workflow automation |
| PostgREST | http://localhost:3001 | REST API |
| PostgreSQL | localhost:5432 | Database |

### 4. Seed Data (after first run)

```bash
docker compose exec app python scripts/seed_data.py
```

## Pages

| Page | Path | Description |
|------|------|-------------|
| Inicio | `/` | KPI summary, favorites, quick actions |
| Consultas | `/consultas` | Saved queries list |
| Nueva Consulta | `/consultas/nueva` | AI chat + results (query builder) |
| Tableros | `/tableros` | Dashboard list |
| **Datos** | `/datos` | **Data Explorer — browse tables, schemas, previews** |

## Data Explorer

The **Datos** page (`/datos`) provides a Redash-like table browser:

- **Sync Status Banner** — shows ingestion status per entity (last sync, record count, status)
- **Table Grid** — clickable cards for each database table (name + row count + size)
- **Detail Panel** with 3 tabs:
  - **Esquema** — column names, types, nullable, defaults, indexes
  - **Vista Previa** — first 50 rows in a paginated DataTable
  - **Perfil** — null %, distinct count per column (data quality overview)

## Data Ingestion

### CLI Tool

```bash
# Demo mode (mock data, no API key needed)
python scripts/generate_mock_data.py
python scripts/ingest_api.py --demo --table messages --tenant demo

# Live API
python scripts/ingest_api.py \
    --api-url https://api.indigitall.com/v1/messages \
    --api-key YOUR_KEY --table messages --tenant visionamos

# Dry run (preview without writing)
python scripts/ingest_api.py --demo --table messages --tenant demo --dry-run
```

### Mapping Files

JSON mapping files in `scripts/mappings/` define API field -> DB column transforms:
- `messages.json`, `contacts.json`, `campaigns.json`, `toques.json`

### n8n Workflows

- `n8n/indigitall-data-sync.json` — Messages + contacts (15-min schedule)
- `n8n/indigitall-campaign-sync.json` — Campaign stats (hourly)

Both workflows include mock data branches for development without API credentials.

## Development

### Local (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

### Project Structure

```
platform/
├── app/
│   ├── main.py              # Dash entry point
│   ├── config.py            # Settings (pydantic-settings)
│   ├── wsgi.py              # Gunicorn entry
│   ├── layouts/             # Page layouts (Dash pages)
│   │   ├── home.py          # / — KPIs + favorites
│   │   ├── query.py         # /consultas/nueva — AI chat
│   │   ├── query_list.py    # /consultas — saved queries
│   │   ├── dashboard_*.py   # /tableros — dashboards
│   │   └── data_explorer.py # /datos — table browser
│   ├── callbacks/           # Dash callbacks
│   ├── services/            # Business logic
│   │   ├── schema_service.py # DB introspection for Data Explorer
│   │   ├── data_service.py   # Conversation analytics
│   │   ├── ai_agent.py       # Claude AI integration
│   │   └── ...
│   ├── middleware/           # Auth, RLS context
│   ├── models/              # SQLAlchemy models
│   └── assets/              # CSS, images
├── dbt/                     # Data transformations
├── n8n/                     # Workflow exports
├── scripts/
│   ├── seed_data.py         # Demo data seeder
│   ├── ingest_api.py        # CLI data ingestion tool
│   ├── generate_mock_data.py # Mock API data generator
│   ├── mappings/            # API -> DB field mappings
│   └── deploy/              # GCP deployment scripts
├── docs/
│   └── DEVELOPER_GUIDE.md   # Onboarding guide
├── docker-compose.yml       # Dev compose
├── docker-compose.prod.yml  # Production overrides
├── Dockerfile
└── requirements.txt
```

## Production Deployment (GCP)

### VM Provisioning

```bash
gcloud compute instances create indigitall-analytics \
    --machine-type=e2-standard-2 \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=50GB \
    --zone=southamerica-east1-b \
    --tags=http-server,https-server
```

### VM Setup

```bash
# SSH into the VM
gcloud compute ssh indigitall-analytics

# Run bootstrap script
sudo bash scripts/deploy/setup_vm.sh
```

### Deploy

```bash
# Clone repo to /opt/indigitall-analytics
# Copy .env.production -> .env (fill in secrets)
# Copy Caddyfile -> /etc/caddy/Caddyfile

# Start services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Seed initial data
docker compose exec app python scripts/seed_data.py

# Start reverse proxy
sudo systemctl restart caddy
```

### Production URLs

| Service | URL |
|---------|-----|
| Analytics | `https://analytics.abstractstudio.co` |
| n8n | `https://n8n-indigitall.abstractstudio.co` |
| Studio | `https://studio-indigitall.abstractstudio.co` |

### Ongoing Deploys

```bash
ssh user@VM_IP 'cd /opt/indigitall-analytics && bash scripts/deploy/deploy.sh'
```

## License

Proprietary — Abstract Studio for indigitall.
