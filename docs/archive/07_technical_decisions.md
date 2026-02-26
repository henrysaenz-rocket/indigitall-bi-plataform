# 07 - Technical Decisions: Indigitall Platform

> **Status:** RECOMMENDATIONS FILLED — PENDING REVIEW
> **Date:** 2026-02-16
> **Context:** Migration from Streamlit demo to production Dash application, white-labeled for indigitall. The platform must consume data from indigitall's 60+ statistics APIs (push, SMS, email, WhatsApp, chat, wallet, journey), store it in a centralized data lake, and serve analytics dashboards with AI-powered natural language queries. Data must refresh hourly.
>
> **Scope & Terminology:**
> - In indigitall's platform, each client is a **"project"** — this is our tenant unit.
> - We do NOT ingest all of indigitall's data. We only ingest data for **projects whose end-clients purchase our analytics product** through indigitall's platform.
> - **Initial launch:** Visionamos customer base — **1 to 10 projects**.
> - **Near-term expansion:** ~7 additional projects from other indigitall clients.
> - **Total near-term scale: ~17 projects max.**

---

## How to Use This Document

Each section presents a technical decision with 3-4 options. For each option, pros and cons are listed. At the bottom of each section, there is a **Final Decision** field. Fill it in once the decision is made, along with the reasoning.

---

## Architecture Overview

The platform has 4 major layers, each requiring technical decisions:

```
┌─────────────────────────────────────────────────────────────────────┐
│  INDIGITALL APIs (Source)                                           │
│  Push Stats, SMS Stats, Email Stats, WhatsApp Stats,               │
│  Chat/Agent Stats, Journey Stats, Wallet Stats, Device Data        │
│  60+ endpoints · JSON + CSV · JWT auth                              │
└────────────────────────────┬────────────────────────────────────────┘
                             │  Decisions #5, #7
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  DATA LAKE (Storage + Transformation)                               │
│                                                                     │
│  RAW Layer ──► STAGING Layer ──► MARTS Layer                        │
│  (API JSON)    (cleaned)         (analytics-ready)                  │
│                                                                     │
│  Decisions #4 (engine), #6 (transforms), #8 (tenancy)              │
└────────────────────────────┬────────────────────────────────────────┘
                             │  Decisions #9, #10
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  APPLICATION (Dash + AI Agent)                                      │
│                                                                     │
│  ┌──────────┐  ┌───────────────┐  ┌──────────────┐                 │
│  │ AI Chat  │  │  Dashboards   │  │ Saved Analyses│                 │
│  │ (NL→SQL) │  │  (Plotly)     │  │ (Folders)     │                 │
│  └──────────┘  └───────────────┘  └──────────────┘                 │
│                                                                     │
│  Decisions #1 (framework), #2 (UI), #3 (auth), #11-12 (AI)         │
└────────────────────────────┬────────────────────────────────────────┘
                             │  Decision #14
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  INDIGITALL CRM (Embedding)                                        │
│  White-labeled iframe / reverse proxy / subdomain                   │
│  JWT auth from indigitall → our platform                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Table of Contents

### Application Layer
1. [Application Framework](#1-application-framework)
2. [UI Component Library](#2-ui-component-library)
3. [Authentication Strategy](#3-authentication-strategy)

### Data Pipeline Layer
4. [Data Lake / Warehouse Engine](#4-data-lake--warehouse-engine)
5. [Data Ingestion & ETL Orchestration](#5-data-ingestion--etl-orchestration)
6. [Data Transformation Pipeline](#6-data-transformation-pipeline)
7. [Data Refresh Strategy](#7-data-refresh-strategy)

### Data Access Layer
8. [Multi-Tenancy Architecture](#8-multi-tenancy-architecture)
9. [Query / Data Access Layer](#9-query--data-access-layer)
10. [Caching Layer](#10-caching-layer)

### AI Layer
11. [AI / LLM Provider](#11-ai--llm-provider)
12. [AI Agent Architecture](#12-ai-agent-architecture)

### Storage & Embedding
13. [Saved Analyses Storage](#13-saved-analyses-storage)
14. [Embedding Strategy](#14-embedding-strategy)

### Infrastructure & Operations
15. [Deployment Infrastructure](#15-deployment-infrastructure)
16. [CI/CD Pipeline](#16-cicd-pipeline)
17. [Monitoring & Logging](#17-monitoring--logging)
18. [Environment & Secrets Management](#18-environment--secrets-management)

---

## 1. Application Framework

> Which Dash distribution do we use?

### Option A: Dash Open Source (Apache 2.0)

| Pros | Cons |
|------|------|
| Free, no licensing cost | No built-in auth, job queue, or design kit |
| Full source access, no vendor lock-in | Must build auth middleware, deployment pipeline yourself |
| Large community, extensive docs | No commercial support |
| Flask under the hood — full ecosystem of Flask extensions | |

### Option B: Dash Enterprise

| Pros | Cons |
|------|------|
| Built-in auth (LDAP, SAML, OAuth) | Expensive (~$15-50K/year depending on seats) |
| App Manager for deployment & scaling | Vendor lock-in to Plotly's infrastructure |
| Snapshot Engine (PDF/image export of dashboards) | Overkill for current scale (5-10 tenants) |
| Design Kit (pre-built enterprise components) | |
| Job Queue for long-running callbacks | |

### Option C: Dash Open Source + Flask Extensions (Hybrid)

| Pros | Cons |
|------|------|
| Free, same as OSS | More initial setup work than Enterprise |
| Flask-Login / Flask-JWT-Extended for auth | Must wire together multiple libraries |
| Celery for background jobs | You own the integration testing burden |
| Full control over every layer | |
| Can upgrade to Enterprise later if needed | |

> **Recommendation: Option C.** Dash Enterprise's $15-50K/year price tag is unjustifiable at your current scale. Pure OSS (Option A) is the same thing as Option C — you'll inevitably add Flask-JWT-Extended and Celery anyway, so plan for it from the start. This gives you zero licensing cost, full control, and a clear upgrade path to Enterprise later if a client demands it.

**Final Decision:**
```
Option: C — Dash Open Source + Flask Extensions (Hybrid)
Reasoning: Enterprise's $15-50K/year is unjustifiable at ~17 projects. OSS + Flask-JWT-Extended
  + Celery gives zero licensing cost, full control, and a clear upgrade path to Enterprise later.
  Flask-JWT-Extended validates indigitall's shared cookie JWT (Decision #3) and sets
  current_setting('app.tenant_id') for RLS enforcement (Decision #8).
Date: 2026-02-16
```

---

## 2. UI Component Library

> Which component library for layout, cards, grids, modals, navbars?

### Option A: Dash Bootstrap Components (DBC)

| Pros | Cons |
|------|------|
| Mature, well-documented | Bootstrap look can feel generic |
| Grid system, cards, navbars, modals, alerts, spinners | Customizing beyond Bootstrap requires CSS overrides |
| Responsive out of the box | Some components less polished than Mantine |
| Large community, many examples | |
| Easy to theme via Bootstrap CSS variables | |

### Option B: Dash Mantine Components (DMC)

| Pros | Cons |
|------|------|
| Modern design system (based on Mantine UI) | Smaller community than Bootstrap |
| Rich components: DatePicker, RingProgress, Stepper, Notifications | Less documentation and examples |
| Built-in dark mode support | Breaking changes between DMC v0.12 and v0.14 |
| Finer-grained theming (MantineProvider) | Learning curve if team knows Bootstrap |

### Option C: Custom CSS (No Component Library)

| Pros | Cons |
|------|------|
| Pixel-perfect match to inDigital design system | Must build every component from scratch |
| Zero dependency bloat | Responsive design is your responsibility |
| No framework-imposed constraints | Significantly more development time |
| Unique look guaranteed | No pre-built modals, dropdowns, navbars |

### Option D: Dash Bootstrap + Custom CSS Overrides (Hybrid)

| Pros | Cons |
|------|------|
| Bootstrap grid/layout + your design tokens | Must maintain an override stylesheet |
| Fast development with pre-built components | Can fight Bootstrap defaults in edge cases |
| Customize colors, fonts, border-radius via CSS vars | Two layers of styling to reason about |
| Closest to current Streamlit demo approach | |

> **Recommendation: Option D.** You already have the inDigital design system defined (colors, fonts, component styles in `styles.py`). DBC gives you the grid, cards, navbars, and modals you need immediately. Override Bootstrap CSS variables with inDigital's tokens (`--bs-primary: #1E88E5`, `--bs-font-sans-serif: Inter`) and you get 90% of the way there. Pure custom CSS (Option C) would triple your development time for marginal visual gains. Mantine (Option B) is tempting but has a smaller Dash ecosystem and less stability between versions.

**Final Decision:**
```
Option: D — Dash Bootstrap + Custom CSS Overrides (Hybrid)
Reasoning: DBC provides grid, cards, navbars, modals out of the box. Override Bootstrap CSS vars
  with inDigital design tokens (--bs-primary: #1E88E5, Inter font). 90% coverage with minimal
  effort. Custom CSS (Option C) would triple dev time for marginal gains.
Date: 2026-02-16
```

---

## 3. Authentication Strategy

> How do users authenticate and how is tenant context established?
>
> **Context:** Since the platform will live on a subdomain provided by indigitall (e.g., `analytics.indigitall.com`), the auth mechanism differs from an iframe embed. The user navigates to a standalone app on a sibling subdomain of indigitall's main CRM.

### Option A: Shared Cookie on Parent Domain (Best for Subdomain)

| Pros | Cons |
|------|------|
| Zero-friction UX — user clicks a link and it just works | **Requires indigitall to set cookies with `Domain=.indigitall.com`** |
| No token in URL (no leakage in browser history, logs, referrer) | Indigitall must include tenant claims in the cookie JWT |
| Cookie refresh handled by indigitall's main app automatically | If indigitall changes their cookie structure, our auth breaks |
| `HttpOnly` + `Secure` flags protect against XSS | Requires same parent domain (`*.indigitall.com`) |
| No redirect dance — simplest UX of all options | |

> **Indigitall dependency:** Indigitall must set their auth JWT cookie with `Domain=.indigitall.com` and include `tenant_id`, `user_id`, `partner_id` claims. This is a one-line change on their backend but requires their dev team's cooperation.

### Option B: URL Redirect with JWT (Simplest Fallback)

| Pros | Cons |
|------|------|
| Works without any cookie changes from indigitall | JWT briefly visible in URL (browser history, server logs) |
| **Indigitall only needs to generate a redirect URL** | Must strip token from URL and set our own session cookie |
| Simple implementation (~30 lines of Flask middleware) | Token refresh requires re-redirect from CRM |
| Compatible with the existing `04_technical_integration_guide.md` flow | Slightly clunky UX (redirect flash) |

> **Indigitall dependency:** Indigitall must implement a redirect endpoint that generates a signed JWT and redirects to `analytics.indigitall.com/?token=eyJ...`. This is what the current integration guide already specifies.

### Option C: OAuth2 Authorization Code Flow (Most Secure)

| Pros | Cons |
|------|------|
| Token never touches the browser (server-to-server exchange) | **Requires indigitall to implement an OAuth2 authorization server** |
| Industry standard, most secure | Significant dev effort from indigitall's team |
| Supports MFA, consent screens, token revocation | More complex integration (redirect → code → token exchange) |
| Best for enterprise compliance requirements | Over-engineered for current stage |

> **Indigitall dependency:** Indigitall must implement OAuth2 endpoints (`/authorize`, `/token`). This is a significant development ask — weeks of work on their side.

### Option D: Flask-Login (Session-Based, Standalone)

| Pros | Cons |
|------|------|
| Works independently — no dependency on indigitall for auth | We manage user accounts, passwords, sessions |
| Simple to implement (50-100 lines) | Duplicate user management (indigitall CRM + our app) |
| Battle-tested Flask extension | Users must log in twice (CRM + analytics) |
| Good for demo/staging environments | No single sign-on experience |

> **Indigitall dependency:** None — but the UX suffers (double login).

> **Recommendation: Option A (Shared Cookie) with Option B as fallback.** Since the app lives on `analytics.indigitall.com` — a sibling subdomain of indigitall's CRM — shared cookies on `.indigitall.com` are the cleanest path. The user logs into indigitall's CRM, the auth cookie is automatically available to our app, and we just validate the JWT and extract the tenant. Zero redirects, zero URL tokens, zero friction. If indigitall can't modify their cookie domain (political or technical reasons), fall back to Option B: a redirect URL with JWT that we immediately strip and convert to our own session cookie. Start the conversation with indigitall's dev team about Option A — it's a one-line backend change for them.

**Final Decision:**
```
Option: A — Shared Cookie on Parent Domain (with Option B as fallback)
Reasoning: Subdomain on analytics.indigitall.com makes shared cookies the cleanest path — user
  logs into CRM, cookie is automatically available to our app, zero redirects. If indigitall
  can't modify their cookie domain, fall back to Option B (URL redirect with JWT). Start the
  conversation with indigitall's dev team about the cookie domain change — it's a one-line
  backend change for them.
  Note: Supabase GoTrue (Decision #4) is NOT used for end-user auth — it is either disabled or
  repurposed for internal/admin access only. Flask-JWT-Extended (Decision #1) validates the
  indigitall shared cookie JWT and extracts project_id for RLS (Decision #8).
Date: 2026-02-16
```

---

## 4. Data Lake / Warehouse Engine

> Where does all indigitall data land after ingestion? This is the core of the platform — we consume from indigitall's APIs (push stats, SMS stats, email stats, WhatsApp stats, chat/agent stats, journey stats, wallet stats, device data) and store it in a centralized data lake for querying.
>
> **Indigitall dependency:** The data volume and structure of indigitall's API responses (JSON vs CSV, nested vs flat, pagination style) influences which engine is optimal. We need sample API responses from indigitall to accurately estimate storage and query requirements.

### Option A: Snowflake

| Pros | Cons |
|------|------|
| Purpose-built for analytics — columnar storage, auto-scaling compute | Expensive at small scale (~$300-500/mo minimum with storage + compute) |
| Native semi-structured data support (VARIANT for raw JSON) | Vendor lock-in — proprietary SQL dialect |
| Built-in Row Access Policies for multi-tenancy | Requires Snowflake account management |
| Time Travel (90-day point-in-time recovery) | Overkill for <10 tenants with moderate data volumes |
| Cortex AI (native LLM integration — could replace external Claude calls) | Learning curve for Snowflake-specific features |
| Already specified in `02_technical_architecture.md` | |
| Separate compute from storage (pay only when querying) | |
| Native support for RAW → STAGING → MARTS pattern | |

### Option B: PostgreSQL (Self-Managed or Managed)

| Pros | Cons |
|------|------|
| Industry standard, team already knows it | Not purpose-built for analytics (row-based, not columnar) |
| Cheap — managed options from $15/mo (Neon, Supabase, Railway) | Slower on large analytical scans vs columnar engines |
| Excellent JSON support (`JSONB`) for raw API responses | No native Time Travel (must set up pg_dump/WAL backups) |
| Row-Level Security (RLS) built in | Manual scaling — no auto-suspend/resume |
| Same engine for both OLTP (app data) and OLAP (analytics) | Will struggle at >50M rows without careful indexing/partitioning |
| Full ecosystem: SQLAlchemy, Alembic, psycopg2, asyncpg | |
| Can add TimescaleDB extension for time-series optimization | |

### Option C: BigQuery (Google Cloud)

| Pros | Cons |
|------|------|
| Serverless — no infrastructure to manage | Vendor lock-in to GCP |
| First 1TB/month of queries free | Unpredictable cost (pay per bytes scanned) |
| Columnar storage, excellent for analytics | Higher latency on small queries (~2s cold start) |
| Native ML and AI integration (BQML) | Less familiar than PostgreSQL for the team |
| Streaming inserts for real-time data | No row-level security (must use authorized views) |
| Supports nested/repeated fields (good for raw API data) | |

### Option D: PostgreSQL + DuckDB (Hybrid OLTP/OLAP)

| Pros | Cons |
|------|------|
| PostgreSQL for app data (saves, auth, tenant config) | Two engines to manage and understand |
| DuckDB for analytical queries (columnar, extremely fast reads) | DuckDB is not a server — process-local only |
| DuckDB can query Parquet files directly from S3 | Less mature ecosystem than pure PostgreSQL |
| Best analytics performance at lowest cost | More complex data pipeline (PG → Parquet → DuckDB) |
| DuckDB has native CSV/JSON ingestion (good for indigitall CSV exports) | |

### Option E: Supabase Self-Hosted

Supabase is an open-source platform built on PostgreSQL. Self-hosting means you run the full Supabase stack on your own infrastructure — no vendor fees, no data limits.

| Pros | Cons |
|------|------|
| PostgreSQL under the hood — all PG knowledge, tools, and dbt models work identically | Heavier deployment: ~12 Docker containers (PG, PostgREST, GoTrue, Realtime, Kong, Storage, Studio, etc.) |
| **RLS as a first-class feature** — visual policy editor in Supabase Studio, project isolation built into the platform | More moving parts to monitor and update than plain PostgreSQL |
| **Auto-generated REST API** (PostgREST) — Dash app and AI agent can query via REST without SQLAlchemy | Self-hosting docs are good but the stack is complex; initial setup takes 2-4 hours |
| **Built-in auth** (GoTrue) — JWT-based, could handle project-level auth natively | GoTrue auth may overlap/conflict with the indigitall JWT flow (Decision #3) |
| **Realtime subscriptions** — dashboards can auto-refresh when n8n finishes a data sync | Realtime adds WebSocket overhead; may not need it if data refreshes hourly |
| **S3-compatible Storage** — saved analyses, CSV exports, PDF reports without separate S3 | Storage service adds another container to manage |
| **Supabase Studio** — web UI for SQL editor, table viewer, RLS policy management, logs | Studio is convenient for debugging but not essential |
| **Fully open source** (Apache 2.0) — no vendor lock-in, no user/project limits | Must manage your own backups, SSL certs, and updates |
| **Zero licensing cost** — only pay for the VPS (~$20-40/mo) | If Supabase project stalls, you maintain 12 containers of someone else's code |
| **Can migrate to Supabase managed** ($25/mo Pro) if self-hosting becomes a burden | Managed Pro has 8GB DB limit — may outgrow it |
| **Consolidates Decisions #8, #9, #13** — RLS, query layer, and storage in one platform | Risk of coupling too many concerns to one platform |

**What the self-hosted Docker Compose looks like:**

```
supabase/
├── docker-compose.yml        # ~200 lines, official template
├── volumes/
│   ├── db/                   # PostgreSQL data
│   └── storage/              # File storage
└── .env                      # Config (JWT secret, DB password, API keys)

Services started:
  supabase-db         (PostgreSQL 15)
  supabase-rest       (PostgREST — auto-generated API)
  supabase-auth       (GoTrue — JWT auth)
  supabase-realtime   (Elixir — live subscriptions)
  supabase-storage    (S3-compatible file storage)
  supabase-studio     (Web dashboard UI)
  supabase-kong       (API gateway / reverse proxy)
  supabase-meta       (PG metadata for Studio)
  supabase-functions  (Deno edge functions — optional)
  supabase-analytics  (Log analytics — optional)
  supabase-vector     (pgvector for embeddings — optional)
```

**Honest assessment of the intimidation factor:**

The ~12 containers sound scary, but in practice:
- Supabase provides an official `docker-compose.yml` that works out of the box
- You run `docker compose up -d` and everything starts
- 4 of the 12 services are optional (functions, analytics, vector, imgproxy)
- The core services (PG, PostgREST, Kong, Studio) are stable and rarely need attention
- Studio gives you a visual UI to manage everything — you're not flying blind
- If a non-PG service breaks (e.g., Realtime), your data and core queries are unaffected — PostgreSQL is the foundation

The real risk isn't complexity — it's **maintenance over time**: keeping 8+ containers updated, debugging inter-service issues when they arise, and managing backups yourself. For a 1-2 person team, this is a real time commitment compared to plain PostgreSQL (1 container) or Supabase managed (zero containers).

> **Recommendation: Option E (Supabase Self-Hosted) OR Option B (Plain PostgreSQL) — depends on your appetite for operational overhead.**
>
> **If you want the most features for zero licensing cost:** Option E. Supabase self-hosted gives you PostgreSQL + RLS dashboard + REST API + auth + storage + realtime in one `docker compose up`. This consolidates Decisions #8 (multi-tenancy via RLS), #9 (query layer via PostgREST), and #13 (storage). The AI agent can query the auto-generated REST API instead of needing SQLAlchemy. At ~17 projects and moderate data volume, a $30/mo VPS handles the full stack. The tradeoff is maintaining ~8 containers.
>
> **If you want the simplest possible setup:** Option B. Plain PostgreSQL (Neon or Railway, $15-25/mo) with RLS policies you write yourself, SQLAlchemy Core for queries, and a separate solution for storage. Fewer moving parts, less to break, less to maintain. You can always migrate to Supabase later — it's the same PostgreSQL underneath.
>
> **Either way:** design the RAW → STAGING → MARTS schema identically. The dbt models, RLS policies, and data pipeline don't change between options. The difference is whether PostgREST, Studio, and Storage are worth the extra containers.

**Final Decision:**
```
Option: E — Supabase Self-Hosted (with Option B as simpler alternative)
Reasoning: Supabase gives PostgreSQL + RLS dashboard + REST API + auth + storage in one
  docker compose up. Consolidates Decisions #8, #9, #13. At ~17 projects a $30/mo VPS handles
  the full stack. The tradeoff is maintaining ~8 containers, but Studio's visual UI and
  PostgREST's auto-generated API reduce app-layer code. If operational overhead becomes a
  concern, plain PostgreSQL (Option B) is the same engine underneath — migration is trivial.
Date: 2026-02-16
```

---

## 5. Data Ingestion & ETL Orchestration

> How do we pull data from indigitall's APIs into the data lake? Indigitall exposes 60+ statistics endpoints (JSON + CSV) across push, SMS, email, WhatsApp, chat, wallet, and journey. We ingest data **only for subscribed projects** — initially 1-10 (Visionamos), growing to ~17. Each project requires its own set of API calls.
>
> **Indigitall dependency:** We need API credentials (JWT auth via `POST /auth`), confirmed rate limits, pagination behavior per endpoint, and a staging/sandbox environment for testing. All endpoints require authentication with indigitall-issued tokens. Critically: we need to confirm whether API calls are scoped **per project** (each project has its own credentials/token) or **per account** (one token accesses all projects with a project filter parameter).

### Option A: n8n (Current Infrastructure)

| Pros | Cons |
|------|------|
| Already running on Abstract Studio's infrastructure | Not purpose-built for data pipelines (it's a general workflow tool) |
| Visual workflow builder — easy to modify and debug | No native data pipeline concepts (incremental loads, schema evolution) |
| Native HTTP Request node for API calls | Single-threaded per workflow — slow for high-volume parallel API calls |
| Cron scheduling built in | No built-in data quality checks or monitoring |
| Can transform data with JavaScript Code nodes | Stateful — harder to scale horizontally |
| Snowflake and PostgreSQL nodes available | No dbt integration |
| Already used by Abstract Studio for other clients (Solfu, CRIS) | |

### Option B: Airflow (Apache)

| Pros | Cons |
|------|------|
| Industry standard for data orchestration | Heavy infrastructure (scheduler, webserver, workers, DB) |
| DAGs as code (Python) — version controlled, testable | Steep learning curve |
| Built-in retry, backfill, and dependency management | Overkill for <20 workflows |
| Massive ecosystem of providers (Snowflake, PG, S3, HTTP) | Requires dedicated DevOps |
| Managed options (Astronomer, MWAA, Cloud Composer) | Managed services are expensive ($300+/mo) |
| Best for complex, interdependent data pipelines | |

### Option C: Dagster

| Pros | Cons |
|------|------|
| Modern data orchestration — assets-first (not task-first) | Newer, smaller community than Airflow |
| Software-defined assets map naturally to RAW → STAGING → MARTS | Learning curve for the asset-based paradigm |
| Built-in data quality checks and observability | Managed service (Dagster Cloud) starts at $100/mo |
| Native dbt integration | Less battle-tested at scale |
| Easier to test than Airflow (standard Python functions) | |
| Better developer experience than Airflow | |

### Option D: n8n for Ingestion + dbt for Transformation (Hybrid)

| Pros | Cons |
|------|------|
| n8n handles API extraction (what it's good at) | Two tools to manage and monitor |
| dbt handles SQL transformations (RAW → STAGING → MARTS) | dbt requires SQL modeling knowledge |
| dbt has built-in testing, documentation, lineage | Must coordinate scheduling between n8n and dbt |
| dbt Cloud free for 1 developer | |
| Clean separation: n8n extracts, dbt transforms | |
| dbt is the industry standard for analytics transformations | |

> **Recommendation: Option D (n8n for Ingestion + dbt for Transformation).** n8n is already running and the team knows it — it's good at calling HTTP APIs, paginating, and dumping results into a database. That's exactly the extraction step. The orchestration pattern is: **master workflow** reads the list of subscribed projects, then **per-project workflows** call indigitall's endpoints for each project and write raw JSON to `RAW.*` tables with a `project_id` column. Then dbt runs SQL models to transform RAW → STAGING → MARTS. At ~17 projects × ~20 key endpoints = ~340 API calls per sync cycle — well within n8n's capacity. dbt Cloud is free for 1 developer, has built-in scheduling, and the testing/documentation features are invaluable for a multi-tenant analytics platform where data quality matters. Airflow (Option B) and Dagster (Option C) are overkill — they replace n8n entirely, which means rewriting existing workflows for Solfu and CRIS.

**Final Decision:**
```
Option: D — n8n for Ingestion + dbt for Transformation (Hybrid)
Reasoning: n8n is already running and the team knows it — good at HTTP API calls, pagination,
  and writing raw JSON into Supabase's PostgreSQL (Decision #4) via the native PG node. dbt
  connects to the same Supabase PG instance via dbt-postgres adapter and handles SQL transforms
  (RAW → STAGING → MARTS) with built-in testing and documentation. At ~17 projects × ~20
  endpoints = ~340 API calls per sync — well within n8n's capacity. dbt Cloud is free for 1
  developer. Airflow and Dagster are overkill and would mean rewriting existing Solfu/CRIS
  workflows.
Date: 2026-02-16
```

---

## 6. Data Transformation Pipeline

> How do we transform raw API responses into queryable analytics tables? Indigitall returns per-channel statistics (sends, clicks, opens, CTR, errors) that need to be normalized, joined, and aggregated for the dashboard.
>
> **Indigitall dependency:** The exact JSON schema per endpoint determines the transformation models. Schema changes on indigitall's API side will break our dbt models — we need a versioned API contract or change notification process.

### Option A: dbt (Data Build Tool)

| Pros | Cons |
|------|------|
| Industry standard for SQL transformations | SQL-only — complex Python transforms not supported |
| RAW → STAGING → MARTS pattern is native to dbt | Requires learning dbt project structure and Jinja templating |
| Built-in testing (not null, unique, accepted values, relationships) | dbt Cloud free tier limited to 1 developer |
| Auto-generated documentation and lineage graphs | Another tool in the stack |
| Version controlled SQL models | |
| Works with Snowflake, PostgreSQL, BigQuery, DuckDB | |
| Incremental models for efficient transforms | |

### Option B: SQL Scripts (Manual Transforms)

| Pros | Cons |
|------|------|
| No additional tools — just SQL files | No built-in testing or documentation |
| Full control, no abstraction | Must manually handle incremental logic |
| Simplest approach for a small team | No lineage tracking |
| Can run via n8n, cron, or any scheduler | Harder to maintain as models grow |
| Zero learning curve | No dependency management between models |

### Option C: Python (Pandas/Polars) Transforms

| Pros | Cons |
|------|------|
| Full Python power for complex transformations | Runs in memory — can't handle very large datasets |
| Great for parsing nested JSON from indigitall APIs | Not optimized for SQL-based data warehouses |
| Team already knows Pandas (current demo uses it) | Harder to maintain than declarative SQL models |
| Can do ML/statistical transforms that SQL can't | Must manage data loading/unloading yourself |
| Good for data quality validation logic | |

### Option D: dbt + Python Models (Hybrid)

| Pros | Cons |
|------|------|
| SQL models for standard transforms (most of the pipeline) | Python models in dbt are slower and less mature |
| Python models for complex logic (NLP, ML, nested JSON parsing) | Requires dbt 1.3+ and specific adapter support |
| Single framework for everything | More complex configuration |
| Best of both worlds | |

> **Recommendation: Option A (dbt).** Your transformations are almost entirely SQL: clean timestamps, normalize channel names, aggregate sends/clicks/CTR, join contacts to messages. Pure SQL handles 95% of this. The RAW → STAGING → MARTS pattern is literally what dbt was built for. Python models (Option D) add complexity you don't need — indigitall's API responses are well-structured JSON, not messy unstructured data. Manual SQL scripts (Option B) will become unmaintainable once you have 20+ models across channels. dbt's built-in tests (`not_null`, `unique`, `accepted_values`) catch data quality issues before they hit the dashboard — critical when you're serving paying tenants.

**Final Decision:**
```
Option: A — dbt (Data Build Tool)
Reasoning: Transformations are almost entirely SQL: clean timestamps, normalize channel names,
  aggregate sends/clicks/CTR, join contacts to messages. RAW → STAGING → MARTS is literally
  what dbt was built for. Built-in tests (not_null, unique, accepted_values) catch data quality
  issues before they hit the dashboard — critical for paying tenants. Manual SQL scripts become
  unmaintainable at 20+ models across channels.
Date: 2026-02-16
```

---

## 7. Data Refresh Strategy

> How often and how do we sync data from indigitall's APIs? The platform has 60+ statistics endpoints across channels. Each indigitall tenant's data needs to stay fresh.
>
> **Indigitall dependency:** Rate limits determine how aggressively we can poll. Webhook event coverage determines if Option D is viable. Incremental query support (`updated_since`, cursor-based pagination) varies per endpoint — we need confirmation from indigitall on which endpoints support it.

### Option A: Hourly Full Refresh (All Endpoints)

| Pros | Cons |
|------|------|
| Simplest logic — pull everything, replace | High API load on indigitall (~60 endpoints × N tenants per hour) |
| No incremental state to manage | Slow for large datasets |
| Always consistent — no stale data | May hit indigitall rate limits |
| Easy to debug and re-run | Wasteful — most data hasn't changed |

### Option B: Hourly Incremental (Cursor-Based)

| Pros | Cons |
|------|------|
| Only fetches changed data since last sync | Must track sync state (last cursor per entity per tenant) |
| Much faster and lighter on indigitall's API | Not all indigitall endpoints support incremental queries |
| Scales well as data grows | More complex error handling (what if sync state corrupts?) |
| Respects rate limits | Statistics endpoints may not support `updated_since` — some may require date range params |

### Option C: Tiered Frequency (Different Intervals per Data Type)

| Pros | Cons |
|------|------|
| Matches data volatility to refresh frequency | More complex scheduling |
| Hot data (chat stats, agent stats) refreshed more often (15 min) | Must define and maintain tier classifications |
| Cold data (campaigns, wallet) refreshed less often (6h/daily) | Different freshness levels can confuse users |
| Optimizes API usage and compute cost | |
| Example tiers: | |
| — **15 min:** Chat stats, agent conversations, active campaign stats | |
| — **1 hour:** SMS/Email/Push/WhatsApp send stats, device stats | |
| — **6 hours:** Campaign configs, journey definitions, wallet projects | |
| — **Daily:** Historical aggregates, pricing stats, full device exports | |

### Option D: Webhook-Driven + Scheduled Backfill

| Pros | Cons |
|------|------|
| Near real-time data via indigitall webhooks | Webhooks can be unreliable (missed events, duplicates) |
| Scheduled backfill catches anything webhooks missed | Must build webhook receiver and event processing |
| Most efficient use of resources | More complex architecture (webhook handler + scheduler) |
| Best data freshness possible | Indigitall webhook coverage may not include all stats endpoints |
| Indigitall does support webhooks (CRUD API confirmed) | Need to validate which events trigger webhooks |

> **Recommendation: Option C (Tiered Frequency).** Not all data changes at the same rate. Chat/agent stats change every minute, but campaign configurations change once a day. At ~17 projects, hourly full refresh (Option A) means ~17 × 60 = ~1,020 API calls per hour — probably manageable, but wasteful. Tiered is smarter: **hourly** for key statistics endpoints (sends, clicks, CTR, agent performance — ~20 endpoints × 17 projects = 340 calls/hour) and **daily** for structural data (campaign configs, journey definitions, wallet projects, full device exports). This keeps API load reasonable and compute costs low. Webhooks (Option D) are worth investigating later — indigitall's webhook API exists, but you'd need to confirm which events it covers before depending on it. Incremental (Option B) is ideal but many of indigitall's statistics endpoints return aggregated data by date range, not cursor-based incremental feeds.

**Final Decision:**
```
Option: C — Tiered Frequency (Different Intervals per Data Type)
Reasoning: Not all data changes at the same rate. Hourly for key statistics endpoints (sends,
  clicks, CTR, agent performance — ~20 endpoints × 17 projects = 340 calls/hour) and daily for
  structural data (campaign configs, journey definitions, wallet projects). Keeps API load
  reasonable and compute costs low. Full hourly refresh (Option A) is wasteful; webhooks
  (Option D) worth investigating later once indigitall confirms event coverage.
Date: 2026-02-16
```

---

## 8. Multi-Tenancy Architecture

> How do we isolate data between indigitall's clients? In indigitall's terminology, each client is a **"project"**. Our tenant = one indigitall project. We only serve projects that have purchased our analytics product through indigitall. Initial scope: 1-10 projects (Visionamos), growing to ~17.
>
> **Indigitall dependency:** Indigitall must provide a `project_id` (their tenant identifier) in API responses and in the auth JWT claims. We need to know: how are new projects onboarded onto the analytics platform? Is it a manual process (we add them) or can indigitall trigger it via API/webhook when a client subscribes?

### Option A: Shared Database, Row-Level Filtering

| Pros | Cons |
|------|------|
| Single database to manage | A bug in the filter = data leak across tenants |
| Simple queries with `WHERE tenant_id = :id` | All tenants compete for the same DB resources |
| Cheapest infrastructure cost | Harder to comply with data residency requirements |
| Easy to add new tenants (just insert data) | Can't give tenants different DB performance tiers |
| PostgreSQL RLS can enforce at the DB level | |

### Option B: Schema-Per-Tenant (Same DB, Separate Schemas)

| Pros | Cons |
|------|------|
| Stronger isolation than row filtering | Schema migrations must run N times (once per tenant) |
| One DB to manage, but data is physically separated | Connection pooling more complex (schema switching) |
| Tenants can have slightly different structures | More complex backup/restore per tenant |
| Easier compliance — can drop a tenant's schema cleanly | Query across tenants requires UNION across schemas |

### Option C: Database-Per-Tenant

| Pros | Cons |
|------|------|
| Strongest isolation — impossible to leak across tenants | Infrastructure cost scales linearly (N databases) |
| Can place tenant DBs in different regions | Connection management complexity |
| Independent backup/restore per tenant | Migrations must run across all DBs |
| Easy to offboard a tenant (delete the DB) | Overkill for <20 tenants |

### Option D: Shared DB + PostgreSQL Row-Level Security (RLS)

| Pros | Cons |
|------|------|
| DB-enforced isolation — app bugs can't leak data | More complex SQL policy setup |
| Single DB, single schema — simple ops | Must set `current_setting('app.tenant_id')` per connection |
| Even a SQL injection can't access other tenants' data | Debugging RLS policies can be tricky |
| Gold standard for multi-tenant SaaS | Slightly more complex onboarding for developers |

> **Recommendation: Option D (Shared DB + PostgreSQL RLS).** For a B2B analytics platform where project data leakage is a deal-breaker, application-level filtering (Option A) is fragile — one missed `WHERE project_id = :id` and you're exposing a client's data to another. RLS enforces isolation at the database level, so even a SQL injection from the AI agent can't cross project boundaries. It's the same single-DB simplicity as Option A but with DB-enforced guarantees. The setup cost is ~20 lines of SQL policy. At ~17 projects, schema-per-project (Option B) and DB-per-project (Option C) are operational overhead for no gain. If you later move to Snowflake, it has Row Access Policies which are the equivalent of PostgreSQL RLS.

**Final Decision:**
```
Option: D — Shared DB + PostgreSQL Row-Level Security (RLS)
Reasoning: For a B2B analytics platform where project data leakage is a deal-breaker, RLS
  enforces isolation at the database level — even a SQL injection from the AI agent can't cross
  project boundaries. Same single-DB simplicity as row filtering but with DB-enforced
  guarantees. Setup cost is ~20 lines of SQL policy. Supabase (Decision #4) makes RLS a
  first-class feature with visual policy editor.
Date: 2026-02-16
```

---

## 9. Query / Data Access Layer

> What sits between the Dash app and the data lake?

### Option A: SQLAlchemy ORM

| Pros | Cons |
|------|------|
| Python standard for DB access | ORM overhead for pure analytics queries |
| Models, migrations (Alembic), connection pooling | Complex queries can be hard to express in ORM syntax |
| Abstracts away DB differences | Learning curve if team prefers raw SQL |
| Type-safe queries, avoids SQL injection by default | |

### Option B: Raw SQL with psycopg2/asyncpg

| Pros | Cons |
|------|------|
| Full SQL power, no abstraction overhead | SQL injection risk if queries aren't parameterized |
| Easiest to port existing Pandas queries | No migration tool — must manage schema changes manually |
| Team writes SQL directly (familiar from Redash-style thinking) | No connection pooling built in (use pgbouncer or manual pool) |
| Best performance for complex analytics | |

### Option C: SQLAlchemy Core (No ORM, Just SQL Builder)

| Pros | Cons |
|------|------|
| SQL builder prevents injection without ORM overhead | Still an abstraction layer to learn |
| Connection pooling included | Less documentation than full ORM |
| Alembic migrations available | Team must learn SQLAlchemy Core API |
| Good middle ground — safe SQL without model classes | |

### Option D: Cube.dev (Semantic Layer)

| Pros | Cons |
|------|------|
| Pre-aggregation and caching built in | Additional service to deploy (Node.js) |
| Semantic data model (measures, dimensions) | New language to learn (Cube schema files) |
| REST + GraphQL API for queries | Overkill if query patterns are simple |
| AI agent can query the semantic layer instead of raw SQL | Adds infrastructure complexity |
| Handles multi-tenancy via security contexts | |

> **Recommendation: Option C (SQLAlchemy Core).** You need SQL flexibility for analytics queries (joins, CTEs, window functions) which rules out the full ORM (Option A) — mapping analytics tables to Python classes adds overhead with no benefit. Raw SQL (Option B) is fast but risky: one un-parameterized string and you have a SQL injection. SQLAlchemy Core gives you the SQL builder that prevents injection, connection pooling out of the box, and Alembic for migrations — all without ORM overhead. You write queries that look like SQL but are safe by construction. Cube.dev (Option D) is interesting but adds a Node.js service for something your Python backend can handle directly.

**Final Decision:**
```
Option: C — SQLAlchemy Core (No ORM, Just SQL Builder) + PostgREST for simple reads
Reasoning: Two query paths, each for what it's best at. PostgREST (from Supabase, Decision #4)
  handles simple CRUD reads — saved analyses, tenant config, listing data — via auto-generated
  REST API with zero Python code. SQLAlchemy Core handles complex analytical queries (joins,
  CTEs, window functions) for dashboards and the AI agent's SQL fallback (Decision #12). Both
  connect to the same Supabase PostgreSQL instance, both respect RLS (Decision #8). Alembic
  handles schema migrations.
Date: 2026-02-16
```

---

## 10. Caching Layer

> How do we cache query results to avoid re-running expensive queries?

### Option A: Redis

| Pros | Cons |
|------|------|
| Industry standard, extremely fast | Another service to deploy and manage |
| TTL-based expiration, pub/sub for invalidation | Data lost on restart (unless persistence enabled) |
| Works as both cache and Celery broker | Memory-bound — cost scales with data size |
| Shared cache across multiple Dash workers | |

### Option B: Flask-Caching with Filesystem Backend

| Pros | Cons |
|------|------|
| Zero additional infrastructure | Not shared across multiple server instances |
| Simple key-value cache on disk | Slower than Redis for high-frequency reads |
| Good enough for single-server deployments | Manual cleanup needed (no auto-TTL on filesystem) |
| Built-in Flask-Caching integration | |

### Option C: Flask-Caching with Redis Backend

| Pros | Cons |
|------|------|
| Flask-Caching API simplicity + Redis performance | Still requires Redis infrastructure |
| Decorator-based caching (`@cache.memoize()`) | Two layers of abstraction |
| Shared across workers | |
| TTL-based expiration | |

### Option D: No Cache (Start Simple)

| Pros | Cons |
|------|------|
| Zero complexity | Every page load re-runs queries |
| Nothing to invalidate or debug | Slower user experience as data grows |
| Fine for <10 concurrent users on small datasets | Will need to add caching eventually |
| Can add caching later when performance demands it | |

> **Recommendation: Option D (No Cache) to start, then Option C (Flask-Caching + Redis) when needed.** Your data refreshes hourly and dashboard queries hit pre-aggregated MARTS tables — these are fast reads on small-to-moderate datasets. Adding Redis day one means another service to deploy, monitor, and invalidate correctly. Start without caching, measure actual query performance, and add Flask-Caching + Redis only when you see P95 response times exceeding 2-3 seconds. When you do add it, Flask-Caching's `@cache.memoize(timeout=3600)` decorator makes it trivial — one line per endpoint. The hourly data refresh cycle is a natural cache TTL.

**Final Decision:**
```
Option: D — No Cache (Start Simple), then C (Flask-Caching + Redis) when needed
Reasoning: Data refreshes hourly and queries hit pre-aggregated MARTS tables — fast reads on
  small datasets. Adding Redis day one means another service to deploy and invalidate. Start
  without caching, measure query performance, add Flask-Caching + Redis when P95 exceeds 2-3s.
  The hourly refresh cycle is a natural cache TTL boundary.
Date: 2026-02-16
```

---

## 11. AI / LLM Provider

> Which LLM powers the natural language analytics agent?

### Option A: Anthropic Claude API (claude-sonnet-4-5-20250929)

| Pros | Cons |
|------|------|
| Strong reasoning and instruction following | API cost (~$3/1M input, $15/1M output tokens for Sonnet) |
| Tool use / function calling support | No built-in SQL generation mode |
| Long context window (200K tokens) | Slightly higher latency than GPT-4o-mini |
| Already referenced in project docs | |
| MCP ecosystem for future tool integrations | |

### Option B: OpenAI GPT-4o

| Pros | Cons |
|------|------|
| Current implementation uses OpenAI (`.env` has `OPENAI_API_KEY`) | API cost (~$2.50/1M input, $10/1M output for GPT-4o) |
| Strong structured output / JSON mode | Vendor lock-in to OpenAI |
| Fast, widely used | Less reliable instruction following than Claude for complex prompts |
| Extensive fine-tuning options | |

### Option C: GPT-4o-mini (Cost Optimized)

| Pros | Cons |
|------|------|
| Very cheap (~$0.15/1M input, $0.60/1M output) | Weaker reasoning than full GPT-4o or Claude |
| Fast response times | May misinterpret complex analytics questions |
| Good enough for simple NL-to-function mapping | Less reliable for edge cases |
| Current agent uses pre-built functions (not raw SQL) — less reasoning needed | |

### Option D: Multi-Provider with Fallback

| Pros | Cons |
|------|------|
| Resilience — if one API is down, use the other | More complex client code (retry logic, adapter pattern) |
| Can route simple queries to cheap model, complex to expensive | Must maintain prompts for multiple models |
| No single vendor dependency | Testing matrix doubles |
| A/B test which model performs better | |

> **Recommendation: Option A (Claude Sonnet).** Claude's instruction-following and tool use are best-in-class for the "understand question → pick the right function → explain the result" pattern your agent uses. The current demo uses OpenAI but the architecture docs already specify Claude. Sonnet 4.5 hits the sweet spot: strong enough for complex analytics questions, fast enough for interactive use (~1-2s), and cost-effective (~$0.01-0.03 per query). GPT-4o-mini (Option C) is tempting for cost but will misinterpret nuanced Spanish-language analytics queries. Multi-provider (Option D) doubles your prompt maintenance for marginal resilience — LLM API uptime is 99.9%+.

**Final Decision:**
```
Option: A — Anthropic Claude API (Claude Sonnet 4.5)
Reasoning: Best-in-class instruction-following and tool use for the "understand question → pick
  function → explain result" pattern. Sonnet 4.5 is the sweet spot: strong reasoning, fast
  (~1-2s), cost-effective (~$0.01-0.03 per query). GPT-4o-mini would misinterpret nuanced
  Spanish-language analytics queries. Multi-provider (Option D) doubles prompt maintenance for
  marginal resilience.
Date: 2026-02-16
```

---

## 12. AI Agent Architecture

> How does the AI agent process natural language queries?

### Option A: Pre-Built Functions (Current Approach)

| Pros | Cons |
|------|------|
| Safe — LLM picks from 13 fixed functions, no raw SQL | Limited to pre-defined analytics |
| Predictable output, easy to test | Adding a new analysis = code change + deploy |
| No SQL injection risk | Can't answer ad-hoc questions outside the function set |
| Already built and working | Users may feel limited |

### Option B: LLM Generates SQL Directly

| Pros | Cons |
|------|------|
| Can answer any question the data supports | SQL injection risk (must sandbox) |
| No pre-built functions to maintain | LLM can generate incorrect or slow SQL |
| Most flexible for end users | Need query validation, row limits, timeout guards |
| Feels like "real AI" — open-ended exploration | Harder to test (infinite possible queries) |

### Option C: Hybrid (Functions + Guarded SQL Fallback)

| Pros | Cons |
|------|------|
| Pre-built functions for common questions (fast, safe) | More complex agent logic (routing decision) |
| SQL fallback for novel questions (flexible) | SQL path still needs guardrails |
| Best of both worlds | Two code paths to maintain |
| LLM decides: "is this a known function or do I need SQL?" | Edge cases in routing can confuse the LLM |

### Option D: Semantic Layer Queries (via Cube.dev or similar)

| Pros | Cons |
|------|------|
| LLM queries a semantic model, not raw SQL | Requires Cube.dev (see Decision #6) |
| Impossible to generate dangerous SQL — queries are against measures/dimensions | Semantic model must be maintained |
| Pre-aggregation makes queries fast | Less flexible than raw SQL |
| Natural fit for AI agents (structured query language) | Additional infrastructure dependency |

> **Recommendation: Option C (Hybrid — Functions + Guarded SQL Fallback).** Your current 13 pre-built functions cover the common questions well and are safe and fast. But users will inevitably ask questions outside that set ("show me the CTR for SMS campaigns in Bogota last Tuesday"). Instead of telling them "I can't do that," the agent should fall back to guarded SQL generation with strict safeguards: READ-ONLY queries, `tenant_id` filter enforcement, row limits, query timeout, and keyword blocklist. The routing logic is simple: Claude classifies whether the question maps to a known function or needs SQL. Pre-built functions handle ~80% of queries instantly; the SQL path handles the remaining 20% with guardrails.

**Final Decision:**
```
Option: C — Hybrid (Functions + Guarded SQL Fallback)
Reasoning: Pre-built functions cover common questions (safe, fast, ~80% of queries). SQL
  fallback handles novel questions via SQLAlchemy Core (Decision #9) with strict guardrails:
  READ-ONLY queries, row limits, query timeout, keyword blocklist. Tenant isolation is enforced
  by PostgreSQL RLS (Decision #8) at the DB level — not app-level WHERE clauses — so even
  malformed AI-generated SQL cannot cross project boundaries. Claude (Decision #11) classifies
  whether the question maps to a known function or needs SQL.
Date: 2026-02-16
```

---

## 13. Saved Analyses Storage

> Where do we persist saved dashboards, queries, and folder structures?

### Option A: Database (PostgreSQL JSON Columns)

| Pros | Cons |
|------|------|
| Transactional — saves are atomic | JSON queries in PG are less intuitive than file reads |
| Backed up with the rest of the DB | Large result sets stored as JSON blobs can bloat the DB |
| Queryable (list all saves for a tenant, search by name) | |
| No separate storage service | |
| Natural fit with multi-tenancy (tenant_id column) | |

### Option B: S3-Compatible Object Storage (S3, MinIO, Cloudflare R2)

| Pros | Cons |
|------|------|
| Unlimited storage, pay-per-use | Additional service to manage |
| Good for large exports (PDFs, CSVs) | Higher latency than local DB for small reads |
| Versioning built in (S3) | Must manage access keys |
| CDN-friendly for shared reports | Listing/searching requires a metadata index |

### Option C: Filesystem (Current Approach)

| Pros | Cons |
|------|------|
| Already built (`storage_service.py`, 369 lines) | Doesn't work with multiple server instances |
| Simple JSON files in folders | No transactional guarantees |
| Zero infrastructure | Backup = backup the disk |
| Fast reads for small datasets | No tenant isolation at storage level |

### Option D: Database Metadata + S3 for Large Files (Hybrid)

| Pros | Cons |
|------|------|
| Metadata in PG (query name, tenant, timestamps, folder) | Two storage systems to maintain |
| Large blobs in S3 (CSV exports, PDF reports) | More complex save/load logic |
| Best of both: fast queries + cheap bulk storage | |
| PG handles structure, S3 handles size | |

> **Recommendation: Option A (Database — PostgreSQL JSON Columns).** You already have PostgreSQL as the data lake (Decision #4). Saved analyses are small JSON documents (query + chart config + metadata) — perfect for a `saved_analyses` table with a `JSONB` column. This gives you tenant isolation for free (`WHERE tenant_id = :id`), atomic saves, and easy querying (list by folder, search by name). The filesystem approach (Option C) breaks with multiple server instances and has no tenant isolation. S3 (Option B) is overkill for JSON documents averaging <10KB each. If you later need PDF/CSV export storage, add S3 just for those large files (Option D) — but don't start there.

**Final Decision:**
```
Option: A — Database (PostgreSQL JSON Columns) in Supabase PG
Reasoning: Saved analyses are small JSON documents (<10KB each) — stored in a saved_analyses
  table with JSONB column in Supabase's PostgreSQL (Decision #4). Tenant isolation enforced by
  RLS (Decision #8). Simple CRUD (list, save, delete) via PostgREST (Decision #9). Filesystem
  (Option C) breaks with multiple instances. S3 (Option B) is overkill — but Supabase Storage
  (included in Decision #4) handles larger files (PDF exports, CSV downloads) when needed.
Date: 2026-02-16
```

---

## 14. Embedding Strategy

> How does inDigital's CRM load our analytics platform?
>
> **Indigitall dependency:** Indigitall must provide a subdomain (e.g., `analytics.indigitall.com`) with a DNS CNAME record pointing to our infrastructure. They must also add a navigation link in their CRM UI that directs users to the analytics subdomain.

### Option A: iframe Embed

| Pros | Cons |
|------|------|
| Simplest integration (one HTML tag) | Cross-origin restrictions (cookies, postMessage) |
| Full isolation — our app runs independently | Feels "embedded" rather than native |
| inDigital only needs to add an iframe to their page | Scroll behavior, responsive sizing can be tricky |
| Auth via URL token parameter | Browser SameSite cookie policies can block auth cookies |

### Option B: Reverse Proxy (analytics.indigital.com → our server)

| Pros | Cons |
|------|------|
| Same domain as inDigital — no CORS, no iframe issues | inDigital must configure their DNS + proxy |
| Feels fully native to end users | More complex infrastructure setup |
| Cookies work normally (same domain) | Debugging is harder (proxy layer in between) |
| Best UX — no embedded "box" feeling | Path routing must not conflict with inDigital's app |

### Option C: Subdomain (analytics.indigital.com, Standalone)

| Pros | Cons |
|------|------|
| Clean separation — our app owns the subdomain | Users leave inDigital's main app to view analytics |
| No iframe or proxy complexity | Less integrated UX (new tab / navigation away) |
| Full control over the domain | Requires SSO to avoid double login |
| Simplest to deploy and maintain | |

### Option D: Micro-Frontend (Web Components / Module Federation)

| Pros | Cons |
|------|------|
| Deepest integration — our widgets live inside inDigital's UI | Extremely complex to implement |
| No iframe, no separate page — truly native | Requires tight coupling with inDigital's frontend stack |
| Shared navigation, theming, user context | CSS conflicts, JS dependency conflicts |
| Best possible UX | Overkill for current stage |

> **Recommendation: Option C (Subdomain).** Indigitall is likely to provide a subdomain (e.g., `analytics.indigitall.com`) that points to our infrastructure. This is the cleanest approach: we fully own the deployment, SSL, and routing with zero dependency on indigitall's frontend team. Users access the analytics platform as a standalone app under indigitall's domain — it feels native without any iframe quirks (no cross-origin issues, no SameSite cookie problems, no scroll/resize hacks). Auth works via SSO or JWT redirect from the main CRM. The only requirement from indigitall is a DNS CNAME record pointing the subdomain to our server. This is a 5-minute ask from their ops team, far simpler than configuring a reverse proxy (Option B) or embedding iframes (Option A). If they later want deeper CRM integration, the subdomain can also serve as the target for an iframe embed — so this doesn't close any doors.

**Final Decision:**
```
Option: C — Subdomain (analytics.indigitall.com, Standalone)
Reasoning: Indigitall provides the subdomain, we fully own deployment, SSL, and routing. Zero
  dependency on indigitall's frontend team. No iframe cross-origin issues, no SameSite cookie
  problems. Auth via shared cookie (Decision #3). Only ask from indigitall: a DNS CNAME record
  (5-minute task). Can also serve as iframe target later if deeper CRM integration is wanted.
Date: 2026-02-16
```

---

## 15. Deployment Infrastructure

> Where does the Dash application run?

### Option A: Docker on VPS (Hetzner, DigitalOcean, AWS Lightsail)

| Pros | Cons |
|------|------|
| Full control, predictable cost ($10-40/month) | You manage OS updates, security patches, backups |
| Docker Compose: Dash + Redis + PostgreSQL | No auto-scaling |
| Same approach as current n8n hosting (Hostinger) | Single point of failure without redundancy |
| Simple — SSH, deploy, done | |

### Option B: AWS ECS / Google Cloud Run (Managed Containers)

| Pros | Cons |
|------|------|
| Auto-scaling based on traffic | More complex setup (IAM, VPC, networking) |
| Managed — no OS patching | Cost can be unpredictable with variable traffic |
| Built-in load balancing, health checks | Vendor lock-in to AWS/GCP |
| Connects to managed DB (RDS, Cloud SQL) | Steeper learning curve for small team |

### Option C: Railway / Render (PaaS)

| Pros | Cons |
|------|------|
| Git push to deploy | Less control over infrastructure |
| Managed PostgreSQL + Redis included | Cost higher than raw VPS at scale |
| Auto-scaling, SSL, custom domains | Vendor-specific constraints |
| Ideal for small teams — minimal DevOps | Can outgrow PaaS limits |
| Railway free tier available for prototyping | |

### Option D: Kubernetes (EKS, GKE, or Self-Hosted)

| Pros | Cons |
|------|------|
| Enterprise-grade orchestration | Massive overkill for current scale |
| Auto-scaling, rolling deploys, self-healing | Requires dedicated DevOps knowledge |
| Multi-region, high availability | Cost: $200+/month minimum for managed K8s |
| Best for 50+ tenants with high traffic | |

> **Recommendation: Option A (Docker on VPS) to start, migrate to Option C (Railway/Render) if DevOps burden grows.** You already self-host n8n on Hostinger — same playbook. A $20-40/month VPS runs Docker Compose with Dash + PostgreSQL + Redis (when needed). Predictable cost, full control, no vendor abstractions to learn. AWS ECS (Option B) and Kubernetes (Option D) are over-engineered for <10 tenants. Railway/Render (Option C) is a good fallback if managing the VPS becomes a time sink — but at your scale, `docker compose up -d` after a `git pull` is 30 seconds of work.

**Final Decision:**
```
Option: A — Docker on VPS (Hetzner, DigitalOcean, or similar)
Reasoning: Already self-hosting n8n on Hostinger — same playbook. Supabase self-hosted
  (Decision #4, ~8 containers) + Dash app + n8n need a VPS with 4-8GB RAM — estimate $40-80/mo
  (Hetzner CX31/CX41 or DigitalOcean 4GB/8GB droplet). All services run via Docker Compose.
  Predictable cost, full control. AWS ECS and Kubernetes are over-engineered for ~17 projects.
  Railway/Render is a good fallback if VPS management becomes a time sink.
Date: 2026-02-16
```

---

## 16. CI/CD Pipeline

> How do we build, test, and deploy changes?

### Option A: GitHub Actions

| Pros | Cons |
|------|------|
| Free for public repos, 2,000 min/month for private | YAML-based config can be verbose |
| Tight GitHub integration (PRs, branch protection) | Debugging failed workflows is clunky |
| Large marketplace of pre-built actions | |
| Can deploy to any target (VPS, AWS, Railway) | |

### Option B: Manual Deploy (SSH + Docker)

| Pros | Cons |
|------|------|
| Zero setup, zero cost | Error-prone (forgot a step, wrong branch) |
| Full control over every step | No audit trail of deployments |
| Fine for 1-2 developers | Doesn't scale with team size |
| `git pull && docker compose up -d` | No automated testing gate |

### Option C: Railway / Render Auto-Deploy

| Pros | Cons |
|------|------|
| Push to main = auto deploy | Only works with supported PaaS platforms |
| Zero CI/CD config needed | No custom test/lint steps (unless you add buildpacks) |
| Preview environments per PR (Render) | Less control over deployment process |
| Fastest path to continuous deployment | |

> **Recommendation: Option B (Manual Deploy) for now, add Option A (GitHub Actions) when the team grows past 2.** With 1-2 developers deploying to a single VPS, `git pull && docker compose up -d` is honest and fast. GitHub Actions adds value when you need automated tests before deploy, multiple environments (staging + prod), or an audit trail — but that's premature at current scale. When you do add CI/CD, GitHub Actions is the clear choice: free tier is generous, it works with any deploy target, and the team already uses GitHub.

**Final Decision:**
```
Option: B — Manual Deploy (SSH + Docker), then A (GitHub Actions) when team grows past 2
Reasoning: With 1-2 developers deploying to a single VPS, git pull && docker compose up -d is
  fast and honest. GitHub Actions adds value when you need automated tests before deploy,
  multiple environments, or audit trails — premature at current scale. When added, GitHub
  Actions is the clear choice (free tier, works with any target).
Date: 2026-02-16
```

---

## 17. Monitoring & Logging

> How do we know when something breaks?

### Option A: Sentry (Error Tracking) + Basic Logging

| Pros | Cons |
|------|------|
| Automatic error capture with stack traces | Free tier limited (5K errors/month) |
| Flask/Dash integration in 3 lines of code | Paid plans start at $26/month |
| Alerts via email/Slack when errors spike | Another third-party dependency |
| Performance monitoring included | |

### Option B: Structured Logging (Python logging → File/Stdout)

| Pros | Cons |
|------|------|
| Zero cost, no external dependency | No alerting — you must check logs manually |
| JSON structured logs for parseability | No error aggregation or deduplication |
| Works with any log aggregator later (ELK, Loki) | Harder to spot trends without a dashboard |
| Good enough for early stage | |

### Option C: Grafana Cloud (Logs + Metrics + Alerts)

| Pros | Cons |
|------|------|
| Full observability stack (Loki + Prometheus + Grafana) | More complex setup |
| Free tier: 50GB logs, 10K metrics/month | Over-engineered for <10 tenants |
| Dashboards for system health | Learning curve |
| Alerting rules (Slack, email, PagerDuty) | |

### Option D: CloudWatch / Cloud Logging (If on AWS/GCP)

| Pros | Cons |
|------|------|
| Native to cloud platform — zero extra setup | Only works if deployed on that cloud |
| Auto-captures container stdout/stderr | Querying logs can be slow and expensive |
| Integrates with cloud alerting | Vendor lock-in |
| Pay-per-use | |

> **Recommendation: Option A (Sentry) + Option B (Structured Logging).** Sentry's free tier (5K errors/month) is more than enough, and the Flask/Dash integration is literally 3 lines of code. You get automatic error capture, stack traces, and Slack alerts without building anything. Combine with Python's `logging` module writing JSON to stdout for operational logs (request timing, sync status, tenant activity). This covers 99% of your monitoring needs. Grafana Cloud (Option C) is overkill — you don't need a metrics dashboard for monitoring a dashboard product. Cloud-specific logging (Option D) locks you into a vendor before you've chosen one.

**Final Decision:**
```
Option: A (Sentry) + B (Structured Logging)
Reasoning: Sentry free tier (5K errors/month) is more than enough. Flask/Dash integration is
  3 lines of code — automatic error capture, stack traces, Slack alerts. Combine with Python
  logging module writing JSON to stdout for operational logs. Grafana Cloud is overkill for
  monitoring a dashboard product. Cloud-specific logging locks into a vendor prematurely.
Date: 2026-02-16
```

---

## 18. Environment & Secrets Management

> How do we handle API keys, DB credentials, and config across environments?

### Option A: .env Files (Current Approach)

| Pros | Cons |
|------|------|
| Simple, familiar, already in use | Must ensure `.env` is in `.gitignore` (risk of committing secrets) |
| Works with python-dotenv (already a dependency) | No audit trail of who changed what |
| Easy to manage per environment (`.env.dev`, `.env.prod`) | Secrets live on disk in plaintext |
| No external service needed | Sharing secrets across team = insecure copy/paste |

### Option B: Cloud Secrets Manager (AWS SSM, GCP Secret Manager)

| Pros | Cons |
|------|------|
| Encrypted at rest, access-controlled | Vendor-specific |
| Audit trail of access and changes | Requires cloud SDK integration |
| Rotation policies for credentials | Cost (small but nonzero) |
| IAM-based access — no secrets in code or env files | Only useful if deployed on that cloud |

### Option C: Docker Secrets + Environment Variables

| Pros | Cons |
|------|------|
| Docker-native, no external service | Only works in Docker Swarm or Compose (v3.1+) |
| Secrets mounted as files, not env vars (more secure) | More complex docker-compose.yml |
| Free, no vendor dependency | Doesn't help during local development |
| Good for self-hosted Docker deployments | |

### Option D: 1Password / Doppler (Team Secrets Manager)

| Pros | Cons |
|------|------|
| Team-wide secrets management with UI | Monthly cost ($5-10/user for 1Password, $18+/mo for Doppler) |
| Auto-inject into local dev, CI/CD, and production | External dependency for deploys |
| Version history, access control | Over-engineered for 1-2 person team |
| Works across any platform | |

> **Recommendation: Option A (.env Files) for now, migrate to Option C (Docker Secrets) when you Dockerize.** You're a 1-2 person team. `.env` files with `python-dotenv` work and are already in place. The key discipline is `.gitignore` — which is already set up. When you deploy via Docker Compose, switch to Docker Secrets for production (secrets mounted as files, not environment variables) while keeping `.env` for local development. Cloud Secrets Manager (Option B) and Doppler (Option D) add cost and complexity that don't pay off until you have multiple developers, multiple environments, and compliance requirements.

**Final Decision:**
```
Option: A — .env Files (now), then C (Docker Secrets) when Dockerized
Reasoning: 1-2 person team, .env files with python-dotenv already work and are in place. Key
  discipline is .gitignore (already set up). When deploying via Docker Compose, switch to Docker
  Secrets for production (secrets as mounted files). Cloud Secrets Manager and Doppler add cost
  and complexity that don't pay off until multiple developers and compliance requirements.
Date: 2026-02-16
```

---

## Indigitall Partner Dependencies

> Everything we need from indigitall to build and launch the platform. These are blockers — without them, the corresponding features cannot be built or deployed.
>
> **Context:** We only ingest data for **subscribed projects** (indigitall's term for a client). Initial launch targets the **Visionamos** customer base (1-10 projects), then ~7 additional projects. The term "project" = our tenant.

### Critical Path (Blocks Development)

| # | Dependency | Description | Blocks | Effort (Indigitall) | Status |
|---|-----------|-------------|--------|---------------------|--------|
| D1 | **API Credentials** | JWT auth credentials (`POST /auth`) for accessing indigitall's REST API. One set for staging, one for production. | Decisions #5, #7 — Data ingestion cannot start | 1 hour | Pending |
| D2 | **Rate Limit Documentation** | Confirmed requests/minute and requests/hour limits per API endpoint, per tenant. | Decision #7 — Cannot design refresh strategy without knowing limits | 30 min (documentation) | Pending |
| D3 | **Staging/Sandbox Environment** | A non-production indigitall environment with sample data for testing API integration and data pipelines. | All data pipeline development | 1-2 hours (provision) | Pending |
| D4 | **Project Identifier Mapping** | Confirm the `project_id` field name and format used in indigitall's API. How does it map to the JWT claims? Is it the same ID used across all endpoints (stats, chat, email, SMS)? | Decisions #3, #8 — Auth and multi-tenancy design | 30 min (documentation) | Pending |
| D5 | **Subdomain Provision** | DNS CNAME record for `analytics.indigitall.com` (or agreed subdomain) pointing to our infrastructure. | Decision #14 — Cannot deploy publicly without this | 5 min (DNS change) | Pending |

### Required for Auth (Blocks User Access)

| # | Dependency | Description | Blocks | Effort (Indigitall) | Status |
|---|-----------|-------------|--------|---------------------|--------|
| D6 | **Shared JWT Secret** | A shared secret key (or public/private key pair) for signing and validating JWT tokens between indigitall's CRM and our platform. | Decision #3 — No authentication without this | 15 min | Pending |
| D7 | **JWT Cookie Domain Change** | Set auth cookie with `Domain=.indigitall.com` instead of default scoping. Must include `project_id`, `user_id`, `partner_id` claims. | Decision #3, Option A — Shared cookie auth | 1-2 hours (backend change) | Pending |
| D8 | **Fallback: Redirect Endpoint** | If D7 is not feasible: implement a `/api/analytics-redirect` endpoint that generates a signed JWT and redirects to `analytics.indigitall.com/?token=eyJ...` | Decision #3, Option B — URL redirect auth | 2-4 hours (backend) | Pending |
| D9 | **Navigation Link in CRM** | Add an "Analytics" link/tab/button in indigitall's CRM UI that navigates users to the analytics subdomain. | Decision #14 — Users need a way to reach the platform | 1-2 hours (frontend) | Pending |

### Required for Data Pipeline (Blocks Data Freshness)

| # | Dependency | Description | Blocks | Effort (Indigitall) | Status |
|---|-----------|-------------|--------|---------------------|--------|
| D10 | **API Endpoint Inventory Confirmation** | Confirm which of the 60+ documented statistics endpoints are available per tenant, and which require additional permissions or plan tiers. | Decision #5 — Cannot build n8n workflows without knowing which endpoints exist | 1-2 hours (documentation) | Pending |
| D11 | **Pagination Behavior per Endpoint** | Confirm pagination style per endpoint: cursor-based, offset-based, or page-based. Include max page size. | Decision #5 — Pagination logic in n8n workflows | 1 hour (documentation) | Pending |
| D12 | **Incremental Query Support** | Confirm which endpoints support `updated_since`, date range filters, or cursor-based incremental fetching. | Decision #7 — Tiered refresh strategy design | 1 hour (documentation) | Pending |
| D13 | **Webhook Event Coverage** | List of events that trigger webhooks. Are statistics updates included, or only transactional events (message sent, campaign created)? | Decision #7, Option D — Webhook-driven refresh | 30 min (documentation) | Pending |
| D14 | **Sample API Responses** | Real or representative JSON responses from key endpoints: push stats, SMS stats, email stats, WhatsApp stats, chat stats, campaign stats. | Decision #6 — Cannot build dbt transformation models without knowing the schema | 1-2 hours (export) | Pending |
| D15 | **API Schema Change Notification** | Agreement on how indigitall will notify us of breaking API changes (email, changelog, versioned API?). | Decision #6 — Prevents silent pipeline failures | 30 min (process agreement) | Pending |

### Required for Tenant Onboarding (Blocks Multi-Tenancy)

| # | Dependency | Description | Blocks | Effort (Indigitall) | Status |
|---|-----------|-------------|--------|---------------------|--------|
| D16 | **Project Provisioning Process** | How do new indigitall projects get added to the analytics platform? When a Visionamos client (or other) subscribes to analytics, who triggers the onboarding — indigitall, the client, or us manually? | Decision #8 — Multi-tenancy onboarding flow | 1 hour (process design) | Pending |
| D17 | **Per-Project API Access** | Confirm whether a single API credential can access all subscribed projects' data (with a project filter), or if each project requires separate credentials/tokens. | Decisions #5, #8 — Ingestion architecture | 30 min (documentation) | Pending |
| D18 | **Subscribed Projects List** | An API endpoint, webhook, or manual process to retrieve the list of projects that have purchased the analytics product. Needed to orchestrate per-project data syncs and control who gets ingested. | Decision #5 — Master sync orchestration | 30 min (documentation) | Pending |

### Nice to Have (Improves Quality, Not Blocking)

| # | Dependency | Description | Improves | Effort (Indigitall) | Status |
|---|-----------|-------------|----------|---------------------|--------|
| D19 | **Historical Data Backfill** | Access to historical data (6-12 months) for the initial Visionamos projects. Without it, the dashboard starts empty on launch day. | Initial launch experience | 1-2 hours (data export or API access) | Pending |
| D20 | **Brand Assets Package** | Official logo files (SVG, PNG), color palette hex codes, font files or names, and component style guidelines for white-labeling. | Decision #2 — UI accuracy | 30 min (shared folder) | Pending |
| D21 | **Test Tenant Accounts** | 2-3 test tenant accounts with realistic sample data for QA and demo purposes. | Testing and staging | 1 hour (provision) | Pending |
| D22 | **Technical Contact** | A named developer on indigitall's team for API questions, integration troubleshooting, and coordination on D6-D9. | All integration work | Ongoing | Pending |

### Dependency Timeline (Suggested Order)

```
Phase 1 — Unblock Development (Week 1)
├── D1  API Credentials
├── D3  Staging Environment
├── D4  Project Identifier Mapping
├── D14 Sample API Responses (from a Visionamos project)
└── D22 Technical Contact

Phase 2 — Unblock Data Pipeline (Week 2-3)
├── D2  Rate Limit Documentation
├── D10 Endpoint Inventory Confirmation
├── D11 Pagination Behavior
├── D12 Incremental Query Support
├── D17 Per-Project API Access
└── D18 Subscribed Projects List (initial Visionamos projects)

Phase 3 — Unblock Deployment (Week 3-4)
├── D5  Subdomain Provision
├── D6  Shared JWT Secret
├── D7  JWT Cookie Domain Change (or D8 as fallback)
├── D9  Navigation Link in CRM
└── D20 Brand Assets Package

Phase 4 — Launch with Visionamos
├── D13 Webhook Event Coverage
├── D15 API Schema Change Notification
├── D16 Project Provisioning Process (for ~7 additional projects)
├── D19 Historical Data Backfill (Visionamos projects)
└── D21 Test Project Accounts
```

---

## Decision Summary

Once all decisions are made, fill in this summary table for quick reference.

| # | Category | Decision | Chosen Option | Date |
|---|----------|----------|---------------|------|
| 1 | App | Application Framework | C — Dash OSS + Flask Extensions | 2026-02-16 |
| 2 | App | UI Component Library | D — DBC + Custom CSS Overrides | 2026-02-16 |
| 3 | App | Authentication Strategy | A — Shared Cookie (B as fallback) | 2026-02-16 |
| 4 | **Data** | **Data Lake / Warehouse Engine** | E — Supabase Self-Hosted | 2026-02-16 |
| 5 | **Data** | **Data Ingestion & ETL Orchestration** | D — n8n + dbt (Hybrid) | 2026-02-16 |
| 6 | **Data** | **Data Transformation Pipeline** | A — dbt | 2026-02-16 |
| 7 | **Data** | **Data Refresh Strategy** | C — Tiered Frequency | 2026-02-16 |
| 8 | Access | Multi-Tenancy Architecture | D — Shared DB + PostgreSQL RLS | 2026-02-16 |
| 9 | Access | Query / Data Access Layer | C — SQLAlchemy Core + PostgREST | 2026-02-16 |
| 10 | Access | Caching Layer | D — No Cache (then C when needed) | 2026-02-16 |
| 11 | AI | AI / LLM Provider | A — Claude Sonnet 4.5 | 2026-02-16 |
| 12 | AI | AI Agent Architecture | C — Hybrid (Functions + SQL) | 2026-02-16 |
| 13 | Storage | Saved Analyses Storage | A — PostgreSQL JSON Columns | 2026-02-16 |
| 14 | Storage | Embedding Strategy | C — Subdomain | 2026-02-16 |
| 15 | Infra | Deployment Infrastructure | A — Docker on VPS | 2026-02-16 |
| 16 | Infra | CI/CD Pipeline | B — Manual Deploy (then A) | 2026-02-16 |
| 17 | Infra | Monitoring & Logging | A+B — Sentry + Structured Logging | 2026-02-16 |
| 18 | Infra | Environment & Secrets Management | A — .env Files (then C) | 2026-02-16 |

---

*Document created: 2026-02-16*
*Last updated: 2026-02-16*
*Author: Abstract Studio*
