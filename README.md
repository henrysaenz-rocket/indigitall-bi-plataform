# inDigitall BI Platform

White-labeled analytics platform for indigitall — Redash-inspired query builder with AI assistant.

## Architecture

- **Frontend:** Plotly Dash + Dash Bootstrap Components
- **Database:** Supabase Self-Hosted (PostgreSQL 15 + PostgREST + RLS)
- **AI Agent:** Claude Sonnet 4.5 (Anthropic) with 13 pre-built functions + SQL fallback
- **Data Pipeline:** n8n (ingestion) + dbt (transformation)
- **Auth:** JWT validation from indigitall's shared cookie

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

## Key Features

The platform includes five primary pages:
- **Inicio** — Dashboard with key metrics
- **Consultas** — Saved queries explorer
- **Nueva Consulta** — Query builder with AI chat assistant
- **Tableros** — Dashboard management
- **Datos** — Data Explorer (table browser with sync status, schema details, data previews, and column profiling)

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
│   ├── config.py             # Settings (pydantic-settings)
│   ├── wsgi.py               # Gunicorn entry
│   ├── layouts/              # Page layouts (Dash pages)
│   ├── callbacks/            # Dash callbacks
│   ├── services/             # Database queries and external integrations
│   ├── middleware/            # Authentication and RLS context
│   ├── models/               # SQLAlchemy models and schemas
│   └── assets/               # CSS, images, and static files
├── dbt/                      # Data transformations
├── n8n/                      # Workflow automation exports
├── scripts/                  # Utility scripts (data ingestion, seeding)
├── docs/                     # Documentation including HENRY_GUIDE.md
├── docker-compose.yml
├── docker-compose.prod.yml   # Production overrides (security-focused)
├── Dockerfile
└── requirements.txt
```

## Deployment

### Development
```bash
docker compose up -d
```

### Production
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

The production override restricts all service ports to `127.0.0.1`, making them accessible only through a reverse proxy (e.g., Caddy) for enhanced security.

## Data Ingestion

Data ingestion flows through:
1. n8n workflows for automated periodic updates
2. Custom CLI scripts with API field-to-database mapping files
3. Multi-tenant support with automatic `tenant_id` field management

## Documentation

- **HENRY_GUIDE.md** — Complete developer guide covering web app modifications and data pipeline workflows
- **Technical Architecture** — System design and component interactions
- **Data Model Design** — Schema definitions and relationships

## License

Proprietary — Abstract Studio for indigitall.
