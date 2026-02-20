# Sprint: Week of Feb 17, 2026 — Visionamos Pilot: UX Sign-off, API Auth, First Dashboard & Production Hosting

## Background

**Abstract Studio** is building a **white-labeled, AI-powered analytics platform** ("Indigitall Analytics") for **Indigitall**, a European CRM/marketing platform. Indigitall resells the platform to their end customers (B2B2B model). The platform is embedded on `analytics.indigitall.com` as a subdomain, white-labeled — no Abstract Studio branding visible to end users.

```
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  Abstract Studio │ ───▶ │    Indigitall    │ ───▶ │ Clientes Finales │
│  (Builds it)     │      │  (Resells it)    │      │    (Uses it)     │
└──────────────────┘      └──────────────────┘      └──────────────────┘
```

**Visionamos** is the **pilot customer** — a Colombian financial cooperative (regulated by SFC - Superintendencia Financiera de Colombia). They use Indigitall's WhatsApp Business platform to communicate with members of their cooperative network (Cooprofesionales, COOVIMAG, Utrahuilca, Cooprudea, Vidasol, etc.). Their pain: fragmented data across WhatsApp and CRM, manual reporting that takes 2+ hours/day, no real-time visibility into chatbot/agent performance.

The platform gives Visionamos operations teams a **natural language AI chat interface** (in Spanish, powered by Claude) to query their data, plus **pre-built dashboards** for campaign analytics (SMS, WhatsApp, Email channels).

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Plotly Dash + Dash Bootstrap Components |
| Backend | Flask (Dash server) + SQLAlchemy Core |
| Database | Supabase Self-Hosted (PostgreSQL 15 + PostgREST + RLS) |
| AI | Anthropic Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`) |
| Data Ingestion | n8n (workflow automation) |
| Transformations | dbt (staging views + mart tables) |
| Auth | Flask-JWT-Extended (shared cookie / URL redirect from Indigitall) |
| Infra | Docker Compose (7 services: db, rest, studio, meta, kong, app, n8n) |
| Repo | `github.com/edelae/indigitall-bi-plataform` (private) |

## Current State

The platform scaffold is complete and running locally. All 6 implementation phases have been committed:

| Commit | Phase | What's Done |
|--------|-------|-------------|
| `7d5b2fd` | Phase 1 | Project scaffold, Docker Compose, Dash shell |
| `76bddd7` | Phase 2 | DB schema (11 tables), services, seed scripts, RLS |
| `3b724fd` | Phase 3 | All Dash pages + callbacks (Home, Query, Dashboard, Saved) |
| `3803afb` | Phase 4 | AI agent — Claude integration, 13 analytics functions, guarded SQL fallback |
| `12ca1ba` | Phase 5 | Auth middleware — dev mode active, JWT structure ready |
| `2378fea` | Phase 6 | dbt models, n8n workflow templates, structured logging |
| `bf0e06d` | Fixes | Docker startup fix, seed data deduplication |

**What works today (locally):**
- `docker compose up -d` starts all 7 services
- Home page loads with real KPI cards (37K messages, 621 contacts, 13 agents seeded from demo CSVs)
- AI Chat page functional with suggestion chips, Claude integration, auto-chart generation
- Dev auth mode active (no login needed, `?tenant=demo` query param)
- Health endpoint returns `{"status":"ok","auth_mode":"dev"}`

**What's stubbed/placeholder:**
- Query List page (shows empty state)
- Dashboard List page (shows empty state)
- Dashboard View page (header + empty widget grid)
- JWT auth coded but not active (needs shared secret from Indigitall — dependency D6/D7)
- n8n workflows have placeholder API URLs (needs Indigitall API credentials — dependency D1)

---

## This Week's Goals

---

### 1. UX Definition & Customer Sign-off

**Objective:** Define the final UX for the Visionamos dashboard and get approval from Indigitall stakeholders before building production views.

**What needs to happen:**
- Design the **Visionamos-specific dashboard layout** — which KPIs, charts, and tables appear on their landing page. The Visionamos use case focuses on:
  - WhatsApp chatbot performance (fallback rate, intent distribution, message volume)
  - Agent performance (handle time, conversations handled, workload distribution)
  - Contact analytics (unique contacts, high-frequency contacts, peak hours)
  - Campaign metrics (sent, delivered, clicks, CTR by channel)
- Create wireframes or mockups (can be Figma, screenshots of the running app, or annotated layouts)
- Define the **navigation flow**: what does a Visionamos user see when they land on the platform? Which page is default? What's in the sidebar/navbar?
- Present to Indigitall for approval — this gates all further frontend work
- Document approved UX as `docs/08_frontend_design.md` in the repo

**Key personas to design for** (from PRD):
- **Maria (Operations Manager):** Wants daily ops summary, fallback rates, quick reporting
- **Carlos (Supervisor):** Wants agent performance, peak hours, intent breakdown
- **Ana (Director):** Wants executive summary, trends, saved/scheduled reports

**Deliverable:** Approved UX design document + stakeholder sign-off

---

### 2. API Authentication for Data Consumption

**Objective:** Establish authenticated access to Indigitall's statistics APIs so we can start ingesting real Visionamos data.

**What needs to happen:**
- Coordinate with Indigitall's dev team to obtain:
  - **D1 — API Credentials:** JWT auth credentials (`POST /auth`) for accessing Indigitall's REST API (staging + production)
  - **D6 — Shared JWT Secret:** For validating JWT tokens between Indigitall's CRM and our platform
  - **D7 — Cookie Domain Change:** Set auth cookie with `Domain=.indigitall.com` including `project_id`, `user_id` claims (or fallback to **D8 — URL redirect with JWT**)
  - **D14 — Sample API Responses:** Real JSON responses from key stats endpoints (push, SMS, WhatsApp, chat) for a Visionamos project
  - **D17 — Per-Project API Access:** Confirm whether one credential accesses all projects or each needs separate tokens
- Test API connectivity with Visionamos project data
- Update n8n workflow templates (`n8n/indigitall-data-sync.json`, `n8n/indigitall-campaign-sync.json`) with real endpoint URLs once credentials are available
- Activate JWT auth mode in the platform if D6/D7 are delivered

**Current auth architecture** (already coded in `app/middleware/auth.py`):
- **Option A (preferred):** Shared cookie on `.indigitall.com` — zero-friction UX, user logs into CRM and our app authenticates automatically
- **Option B (fallback):** URL redirect — Indigitall generates signed JWT and redirects to `analytics.indigitall.com/?token=eyJ...`
- The middleware extracts `project_id` from JWT claims and sets PostgreSQL RLS context per request

**Deliverable:** Working API auth + at least one successful data pull from Indigitall's API for Visionamos

---

### 3. First Visionamos Dashboard

**Objective:** Build the first production dashboard for Visionamos using real or seeded data, ready for demo.

**What needs to happen:**
- Implement the Dashboard View page (currently stubbed at `app/layouts/dashboard_view.py` + `app/callbacks/dashboard_view_cb.py`)
- Build the **"Control de Conversaciones"** dashboard for Visionamos with:
  - **KPI row:** Total messages, Unique contacts, Active agents, Fallback rate (with health indicator: green <15%, yellow 15-25%, red >25%)
  - **Charts:** Messages over time (line), Messages by direction (bar — Inbound/Bot/Agent), Messages by hour (bar — peak hours), Intent distribution (horizontal bar), Agent performance (table + bar)
  - **Filters:** Date range picker, Entity/project dropdown (for Visionamos sub-entities like Cooprofesionales, COOVIMAG, etc.)
  - **Export:** CSV download per table
- Wire the dashboard to `DataService` methods (already implemented in `app/services/data_service.py`):
  - `get_summary_stats()`, `get_messages_over_time()`, `get_messages_by_direction()`, `get_messages_by_hour()`, `get_intent_distribution()`, `get_agent_performance()`, `get_fallback_rate()`, `get_top_contacts()`
- Charts are already buildable via `ChartService` (`app/services/chart_service.py` — 588 lines of Plotly code, ported from Demo)
- If real API data isn't available yet, use the seeded demo data (37K messages across Visionamos entities)

**Deliverable:** Working dashboard page at `/tableros/visionamos` with real charts and KPIs

---

### 4. Production Hosting — Get the App Online

**Objective:** Deploy the platform to a VPS so it's accessible at a public URL, ready for Visionamos demo and eventually at `analytics.indigitall.com`.

**Architecture Decision:** Docker on VPS (Decision #15 from technical decisions doc). Same playbook as the existing n8n instance already running on Hostinger (`n8n.srv956580.hstgr.cloud`).

**Infrastructure Requirements:**

| Resource | Spec | Why |
|----------|------|-----|
| VPS Provider | Hetzner CX31/CX41, DigitalOcean 4GB+, or second Hostinger VPS | Need 4-8GB RAM for 7 Docker containers |
| RAM | 4GB minimum, 8GB recommended | PostgreSQL + 6 other services |
| Disk | 40-80GB SSD | DB storage + Docker images |
| OS | Ubuntu 22.04 LTS | Docker support, team familiarity |
| Cost estimate | $20-40/month (Hetzner) or $40-80/month (DigitalOcean) | Existing Hostinger plan is $12/mo for n8n only |

**Step-by-step deployment:**

**Step 1 — Provision VPS**
- Create a VPS instance (Hetzner recommended for price/performance, or use existing Hostinger account)
- Ubuntu 22.04 LTS, minimum 4GB RAM, 40GB SSD
- Configure SSH key access (disable password auth)
- Set up basic firewall (UFW): allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS)

**Step 2 — Install Docker**
```bash
# On the VPS:
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
# Log out and back in
```

**Step 3 — Install Caddy (reverse proxy + auto-SSL)**
```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install caddy
```

**Step 4 — Clone the repo and configure**
```bash
git clone git@github.com:edelae/indigitall-bi-plataform.git /opt/indigitall
cd /opt/indigitall

# Create production .env from template
cp .env.example .env
# Edit .env with production values:
#   - Strong FLASK_SECRET_KEY and JWT_SECRET_KEY (generate with: openssl rand -hex 32)
#   - Strong POSTGRES_PASSWORD
#   - Real ANTHROPIC_API_KEY
#   - DEBUG=false
#   - AUTH_MODE=dev (for now, switch to jwt when D6/D7 arrive)
```

**Step 5 — Harden docker-compose for production**
- Remove `version: "3.8"` line (deprecated)
- On the `app` service: remove the dev volume mount (`./app:/app/app`) so the built image is used instead of hot-reload
- Ensure `restart: unless-stopped` is on all services (already set)
- Restrict exposed ports — only Dash (8050) needs to be proxied externally. PostgreSQL (5432), PostgREST (3001), Studio (3000), n8n (5678) should bind to `127.0.0.1` only:
  ```yaml
  # Example: change "5432:5432" to "127.0.0.1:5432:5432"
  ```

**Step 6 — Configure Caddy reverse proxy**

Create `/etc/caddy/Caddyfile`:
```
# Temporary domain until indigitall provides analytics.indigitall.com
indigitall-analytics.your-domain.com {
    reverse_proxy localhost:8050
}

# When indigitall provides the subdomain (dependency D5):
# analytics.indigitall.com {
#     reverse_proxy localhost:8050
# }
```

Caddy automatically provisions SSL certificates via Let's Encrypt — no manual certbot needed.

**Step 7 — Start everything**
```bash
cd /opt/indigitall
docker compose up -d --build
sudo systemctl restart caddy
```

**Step 8 — Seed the database**
```bash
docker compose run --rm app python scripts/seed_data.py
```

**Step 9 — Verify**
- `curl https://indigitall-analytics.your-domain.com/health` should return `{"status":"ok","auth_mode":"dev"}`
- Open the URL in browser — dashboard should load with demo data

**Step 10 — DNS for final domain (blocked on Indigitall — dependency D5)**
- Indigitall creates a CNAME record: `analytics.indigitall.com → <VPS-IP-or-hostname>`
- Update Caddyfile with the real domain
- `sudo systemctl reload caddy` — SSL auto-provisions

**Deployment workflow going forward:**
```bash
# SSH into VPS, then:
cd /opt/indigitall
git pull origin main
docker compose up -d --build
# Done. ~30 seconds.
```

**What's NOT needed yet (premature):**
- GitHub Actions CI/CD (add when team > 2 people)
- Kubernetes (add when > 50 tenants)
- Load balancer / auto-scaling (single VPS handles ~17 projects fine)
- Managed DB (Supabase self-hosted is free, managed Pro is $25/mo if needed later)

**Deliverable:** App accessible via HTTPS on a public URL with demo data loaded

---

## Files & Directories Reference

```
platform/
├── app/
│   ├── main.py                    # Dash app entry, navbar, layout, callback imports
│   ├── config.py                  # pydantic-settings (.env loading)
│   ├── wsgi.py                    # Gunicorn entry point
│   ├── middleware/auth.py         # Auth middleware (dev + JWT modes)
│   ├── layouts/                   # Page layouts (Dash register_page)
│   │   ├── home.py                # / — KPIs + quick actions
│   │   ├── query.py               # /consultas/nueva — AI chat + results
│   │   ├── query_list.py          # /consultas — saved queries (stubbed)
│   │   ├── dashboard_view.py      # /tableros/<id> — dashboard (stubbed)
│   │   └── dashboard_list.py      # /tableros — dashboard list (stubbed)
│   ├── callbacks/                 # Dash callbacks per page
│   ├── services/
│   │   ├── data_service.py        # SQLAlchemy queries → DataFrames
│   │   ├── toques_data_service.py # Campaign/toques analytics queries
│   │   ├── chart_service.py       # Plotly chart builders (588 lines, ready)
│   │   ├── ai_agent.py            # Claude integration + 13 functions + SQL fallback
│   │   └── storage_service.py     # Saved queries/dashboards CRUD
│   ├── models/
│   │   ├── database.py            # SQLAlchemy engine, sessions, RLS helpers
│   │   └── schemas.py             # 11 table definitions
│   └── assets/styles.css          # Full design system (CSS variables, responsive)
├── dbt/                           # Transformation models (staging + marts)
├── n8n/                           # Workflow templates (placeholder URLs)
├── scripts/seed_data.py           # CSV → PostgreSQL seeder
├── docker-compose.yml             # 7 services
└── .env                           # Environment config (dev mode)
```

## Key Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Visionamos PRD | `ai_studio/Indigital/PRD_visionamos_Pilot.md` | Full pilot requirements, personas, success metrics |
| Technical Decisions | `ai_studio/Indigital/docs/07_technical_decisions.md` | 18 architecture decisions with rationale |
| Indigitall SOW (ES) | `contracts/customer_contracts/indigitall/sow-indigitall-partnership-es.md` | Partnership contract, pricing, SLA |
| Full Solution PRD | `ai_studio/Indigital/PRD_InDigital_FullSolution.md` | Vision for scaling beyond Visionamos |
| Indigitall Dependencies | `docs/07_technical_decisions.md` § "Indigitall Dependencies" | D1-D22 dependency tracker |

## Blocked On (From Indigitall)

| ID | Dependency | Impact | Est. Effort (their side) |
|----|-----------|--------|--------------------------|
| D1 | API Credentials | Can't ingest real data | 1 hour |
| D5 | Subdomain Provision | Can't use `analytics.indigitall.com` (use temp domain until then) | 5 min DNS change |
| D6 | Shared JWT Secret | Can't activate production auth | 15 min |
| D7 | Cookie Domain Change | Can't do seamless auth (fallback: D8 URL redirect) | 1-2 hours |
| D14 | Sample API Responses | Can't validate dbt transformation models | 1-2 hours |
| D19 | Historical Data Backfill | Dashboard starts empty without 6-12 months of history | 1-2 hours |
| D22 | Technical Contact | Need a named dev for integration questions | Ongoing |

## Definition of Done

- [ ] UX design approved by Indigitall stakeholder (documented in repo)
- [ ] API credentials received and tested (or clear timeline communicated)
- [ ] JWT auth tested end-to-end (or fallback documented if D6/D7 delayed)
- [ ] Visionamos dashboard renders with KPIs + charts (real or demo data)
- [ ] VPS provisioned and SSH accessible
- [ ] Docker Compose running on VPS with all 7 services healthy
- [ ] Caddy configured with SSL on a public URL (temporary or final domain)
- [ ] App accessible via HTTPS with demo data loaded
- [ ] Deployment process documented in repo README
- [ ] All changes committed and pushed to `main`
