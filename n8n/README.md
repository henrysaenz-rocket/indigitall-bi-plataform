# n8n Workflow Templates

This directory contains n8n workflow JSON templates for data ingestion.

## Workflows

### `indigitall-data-sync.json`
Syncs conversation data (messages, contacts, agents) from indigitall API to PostgreSQL.

**Schedule (tiered):**
- Messages: every 15 minutes (real-time chat data)
- Contacts/Agents: hourly (structural data, slower to change)
- Daily stats: daily at 02:00 UTC (aggregation)

### `indigitall-campaign-sync.json`
Syncs campaign data (toques, campaigns) from indigitall API to PostgreSQL.

**Schedule:** Hourly

## Status

These templates use **placeholder API URLs** because indigitall API access (D1, D2, D14) is pending.
Once API credentials and sample responses arrive, update:

1. The HTTP Request nodes with real API URLs
2. The authentication headers
3. The JSON-to-table mapping in Set nodes
4. The pagination logic

## How to Import

1. Open n8n at `http://localhost:5678`
2. Go to Workflows > Import from File
3. Select the `.json` file
4. Update credentials and API URLs
5. Activate the workflow

## Environment Variables

These workflows reference environment variables set in `docker-compose.yml`:

| Variable | Description |
|----------|-------------|
| `DB_HOST` | PostgreSQL host (default: `db`) |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `INDIGITALL_API_URL` | Base URL for indigitall API (TBD) |
| `INDIGITALL_API_KEY` | API key for indigitall (TBD) |
