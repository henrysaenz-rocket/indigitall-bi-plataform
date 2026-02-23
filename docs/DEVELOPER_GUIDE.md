# Developer Guide — inDigitall BI Platform

## Accessing the Platform

### Production URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Analytics | `https://analytics.abstractstudio.co` | Main dashboard + AI chat |
| n8n | `https://n8n-indigitall.abstractstudio.co` | Workflow automation |
| Studio | `https://studio-indigitall.abstractstudio.co` | Database admin (backup) |

### Local Development

```bash
# Clone and enter the project
cd Indigital/platform

# Start all services
docker compose up -d

# Local URLs:
# Dash App:       http://localhost:8050
# n8n:            http://localhost:5678
# Supabase Studio: http://localhost:3000
```

### Seed Data (first run)

```bash
docker compose exec app python scripts/seed_data.py
```

---

## Using the Data Explorer

Navigate to **Datos** in the top navbar (or go to `/datos`).

### Table Browser

- Shows all database tables with row counts and sizes
- Click any table card to open the detail panel

### Detail Panel Tabs

| Tab | Description |
|-----|-------------|
| **Esquema** | Column names, data types, nullable, defaults, indexes |
| **Vista Previa** | First 50 rows with pagination and search |
| **Perfil** | Null %, distinct count per column (data quality overview) |

### Sync Status Banner

Shows the ingestion status for each data entity (messages, contacts, campaigns). Status badges:
- **completed** (green) — last sync succeeded
- **running** (blue) — sync in progress
- **error** (red) — last sync failed
- **pending** (gray) — never synced

---

## Configuring Data Sources

### When API Credentials Arrive

1. Update `.env` with the indigitall API credentials:
   ```
   INDIGITALL_API_URL=https://api.indigitall.com
   INDIGITALL_API_KEY=your-api-key-here
   ```

2. Update mapping files in `scripts/mappings/` if field names differ from placeholders

3. Test with dry run:
   ```bash
   docker compose exec app python scripts/ingest_api.py \
       --api-url https://api.indigitall.com/v1/messages \
       --api-key YOUR_KEY --table messages --tenant visionamos --dry-run
   ```

4. Run actual ingestion:
   ```bash
   docker compose exec app python scripts/ingest_api.py \
       --api-url https://api.indigitall.com/v1/messages \
       --api-key YOUR_KEY --table messages --tenant visionamos
   ```

### Mapping Files

Located in `scripts/mappings/`. Each JSON file defines:
- `fields` — API field name -> database column name
- `defaults` — default values for missing fields
- `transforms` — type conversions (`bool`, `int`, `date_only`, `lowercase`)

Available mappings:
- `messages.json` — Message/conversation data
- `contacts.json` — Contact records
- `campaigns.json` — Campaign metadata
- `toques.json` — Campaign daily statistics

---

## Running Ingestion Scripts

### Demo Mode (No API Key Needed)

```bash
# Generate mock data
docker compose exec app python scripts/generate_mock_data.py

# Ingest mock data
docker compose exec app python scripts/ingest_api.py --demo --table messages --tenant demo
docker compose exec app python scripts/ingest_api.py --demo --table contacts --tenant demo
docker compose exec app python scripts/ingest_api.py --demo --table campaigns --tenant demo
docker compose exec app python scripts/ingest_api.py --demo --table toques_daily --tenant demo
```

### Live API Mode

```bash
python scripts/ingest_api.py \
    --api-url https://api.indigitall.com/v1/messages \
    --api-key $INDIGITALL_API_KEY \
    --table messages \
    --tenant visionamos \
    --mapping scripts/mappings/messages.json
```

### CLI Options

| Flag | Description |
|------|-------------|
| `--demo` | Use mock JSON files instead of real API |
| `--dry-run` | Show what would be inserted without writing |
| `--table` | Target database table (required) |
| `--tenant` | Tenant ID for multi-tenant isolation (required) |
| `--mapping` | Path to JSON mapping file |
| `--limit` | Records per page (default: 1000) |
| `--max-pages` | Max pages to fetch (default: 100) |

---

## Git Workflow

### Branches

- `main` — production code, deployed to GCP VM
- Feature branches — `feature/data-explorer`, `fix/sync-error`, etc.

### Deploying Changes

```bash
# On the VM:
cd /opt/indigitall-analytics
bash scripts/deploy/deploy.sh
```

This script:
1. Pulls latest code from git
2. Rebuilds the Dash app container
3. Restarts all services
4. Runs database migrations
5. Checks health endpoint

---

## Troubleshooting

### "Cannot connect to database"

```bash
# Check if PostgreSQL is running
docker compose ps db

# Check logs
docker compose logs db --tail 20

# Restart database
docker compose restart db
```

### "Table not found in Data Explorer"

Tables must be in the `ALLOWED_TABLES` whitelist in `app/services/schema_service.py`. Add new table names there after creating them.

### "Sync status shows error"

```bash
# Check what the error was
docker compose exec db psql -U postgres -c "SELECT * FROM sync_state WHERE status = 'error';"

# Reset sync state
docker compose exec db psql -U postgres -c "UPDATE sync_state SET status = 'pending' WHERE entity = 'messages';"

# Re-run ingestion
docker compose exec app python scripts/ingest_api.py --demo --table messages --tenant demo
```

### "AI chat not responding"

Check if the Anthropic API key is configured:
```bash
docker compose exec app python -c "from app.config import settings; print(settings.has_ai_key)"
```

If `False`, set `ANTHROPIC_API_KEY` in `.env` and restart:
```bash
docker compose restart app
```

### "n8n workflows not running"

```bash
# Check n8n logs
docker compose logs n8n --tail 20

# Verify n8n is accessible
curl http://localhost:5678/healthz
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs app --tail 50

# Caddy (reverse proxy)
sudo tail -f /var/log/caddy/analytics.log
```
