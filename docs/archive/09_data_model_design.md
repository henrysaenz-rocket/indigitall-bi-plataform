# 09 — Data Model Design Document

**Version:** 1.0 — Draft for Review
**Date:** 2026-02-16
**Status:** PENDING REVIEW

---

## 1. Entity-Relationship Overview

The platform has two data domains (**Conversations** and **Campaigns**) plus an **Application** domain for platform state. Every table includes `tenant_id` for Row-Level Security.

```
                            ┌──────────────────┐
                            │   sync_state     │
                            │   (ETL tracking) │
                            └──────────────────┘

 ═══════════════ CONVERSATIONS DOMAIN ═══════════════    ═══════════ CAMPAIGNS DOMAIN ═══════════

 ┌───────────────┐    ┌───────────────┐                  ┌──────────────────┐
 │   contacts    │◄──┐│   agents      │                  │   campaigns      │
 │   (dim)       │   ││   (dim)       │                  │   (dim)          │
 └───────┬───────┘   │└───────────────┘                  └────────┬─────────┘
         │           │       ▲                                    │
         │ 1:N       │       │ N:1                                │ 1:N
         ▼           │       │                                    ▼
 ┌───────────────┐   │       │                           ┌──────────────────┐
 │   messages    │───┘───────┘                           │  toques_daily    │
 │   (fact)      │                                       │  (fact)          │
 └───────┬───────┘                                       └────────┬─────────┘
         │                                                        │
         │ aggregated                                             │ aggregated
         ▼                                                        ▼
 ┌───────────────┐                                       ┌──────────────────┐
 │  daily_stats  │                                       │ toques_heatmap   │
 │  (agg)        │                                       │ (agg)            │
 └───────────────┘                                       └──────────────────┘
                                                                  │
                                                                  │ derived
                                                                  ▼
                                                         ┌──────────────────┐
                                                         │ toques_usuario   │
                                                         │ (agg)            │
                                                         └──────────────────┘

 ═══════════════ APPLICATION DOMAIN ═══════════════

 ┌───────────────┐    ┌───────────────┐    ┌──────────────────┐
 │ saved_queries │    │  dashboards   │    │ dashboard_widgets │
 └───────────────┘    └───────┬───────┘    └──────────────────┘
                              │ 1:N               ▲
                              └───────────────────┘
```

---

## 2. Table Definitions

### 2.1 Conversations Domain

#### `messages` — Fact table (source of truth for chat analytics)

**Source:** WhatsApp Business API via n8n (currently: `messages.csv`, 50,586 rows)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | `SERIAL` | NO | Internal PK |
| `tenant_id` | `VARCHAR(50)` | NO | Tenant isolation key (= entity in CSV) |
| `message_id` | `VARCHAR(100)` | NO | Source system message ID |
| `timestamp` | `TIMESTAMPTZ` | NO | Exact message timestamp |
| `date` | `DATE` | NO | Date portion (for grouping) |
| `hour` | `SMALLINT` | NO | Hour 0-23 (for hourly analysis) |
| `day_of_week` | `VARCHAR(10)` | NO | Monday, Tuesday, etc. |
| `send_type` | `VARCHAR(30)` | YES | input, dialogflow, operator, agent_notification |
| `direction` | `VARCHAR(20)` | NO | Inbound, Bot, Agent, Outbound, System |
| `content_type` | `VARCHAR(30)` | YES | text, interactive, quickReplyEvent, event |
| `status` | `VARCHAR(20)` | YES | Message delivery status |
| `contact_name` | `VARCHAR(255)` | YES | Contact display name |
| `contact_id` | `VARCHAR(100)` | YES | FK reference to contacts |
| `conversation_id` | `VARCHAR(100)` | YES | Groups messages into conversations |
| `agent_id` | `VARCHAR(100)` | YES | FK reference to agents (NULL if bot) |
| `close_reason` | `VARCHAR(100)` | YES | How conversation ended |
| `intent` | `VARCHAR(200)` | YES | Dialogflow intent name |
| `is_fallback` | `BOOLEAN` | NO | True = bot didn't understand (Default: false) |
| `message_body` | `TEXT` | YES | Message content (truncated, no PII in production) |
| `is_bot` | `BOOLEAN` | NO | True if message from bot |
| `is_human` | `BOOLEAN` | NO | True if message from human agent |
| `wait_time_seconds` | `INTEGER` | YES | Time waiting for agent assignment |
| `handle_time_seconds` | `INTEGER` | YES | Total agent handling time |

**Indexes:**
- `idx_messages_tenant_date` on `(tenant_id, date)`
- `idx_messages_tenant_direction` on `(tenant_id, direction)`
- `idx_messages_contact` on `(tenant_id, contact_id)`
- `idx_messages_conversation` on `(tenant_id, conversation_id)`
- `idx_messages_timestamp` on `(tenant_id, timestamp DESC)`

**Primary Key:** `id`
**Unique:** `(tenant_id, message_id)`
**RLS Policy:** `tenant_id = current_setting('app.current_tenant')`

---

#### `contacts` — Dimension table

**Source:** Derived from messages (currently: `contacts.csv`, 623 rows)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | `SERIAL` | NO | Internal PK |
| `tenant_id` | `VARCHAR(50)` | NO | Tenant isolation key |
| `contact_id` | `VARCHAR(100)` | NO | Source system contact ID |
| `contact_name` | `VARCHAR(255)` | YES | Display name |
| `total_messages` | `INTEGER` | NO | Lifetime message count (Default: 0) |
| `first_contact` | `DATE` | YES | First message date |
| `last_contact` | `DATE` | YES | Most recent message date |
| `total_conversations` | `INTEGER` | NO | Lifetime conversation count (Default: 0) |

**Primary Key:** `id`
**Unique:** `(tenant_id, contact_id)`
**RLS Policy:** `tenant_id = current_setting('app.current_tenant')`

---

#### `agents` — Dimension table

**Source:** Derived from messages (currently: `agents.csv`, 13 rows)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | `SERIAL` | NO | Internal PK |
| `tenant_id` | `VARCHAR(50)` | NO | Tenant isolation key |
| `agent_id` | `VARCHAR(100)` | NO | Source system agent ID |
| `total_messages` | `INTEGER` | NO | Messages handled (Default: 0) |
| `conversations_handled` | `INTEGER` | NO | Conversations handled (Default: 0) |
| `avg_handle_time_seconds` | `INTEGER` | YES | Average handling time |

**Primary Key:** `id`
**Unique:** `(tenant_id, agent_id)`
**RLS Policy:** `tenant_id = current_setting('app.current_tenant')`

---

#### `daily_stats` — Pre-aggregated summary

**Source:** Aggregated from messages daily (currently: `daily_stats.csv`, 29 rows)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | `SERIAL` | NO | Internal PK |
| `tenant_id` | `VARCHAR(50)` | NO | Tenant isolation key |
| `date` | `DATE` | NO | Aggregation date |
| `total_messages` | `INTEGER` | NO | Messages that day |
| `unique_contacts` | `INTEGER` | NO | Distinct contacts |
| `conversations` | `INTEGER` | NO | Distinct conversations |
| `fallback_count` | `INTEGER` | NO | Count of is_fallback=true messages |

**Primary Key:** `id`
**Unique:** `(tenant_id, date)`
**RLS Policy:** `tenant_id = current_setting('app.current_tenant')`

**Data Quality Note:** In current CSV, `fallback_count` stores concatenated strings instead of integers. The seed script and dbt staging model must fix this: cast to integer or re-derive from `messages` table as `COUNT(*) WHERE is_fallback = true`.

---

### 2.2 Campaigns Domain

#### `toques_daily` — Fact table (daily campaign metrics by channel/project)

**Source:** Campaign API via n8n (currently: `toques_daily.csv`, 1,061 rows)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | `SERIAL` | NO | Internal PK |
| `tenant_id` | `VARCHAR(50)` | NO | Tenant isolation key |
| `date` | `DATE` | NO | Metric date |
| `canal` | `VARCHAR(30)` | NO | SMS, WhatsApp, Email, Push, In App/Web |
| `proyecto_cuenta` | `VARCHAR(100)` | NO | Project/account name |
| `enviados` | `INTEGER` | NO | Messages/impressions sent (Default: 0) |
| `entregados` | `INTEGER` | NO | Successfully delivered (Default: 0) |
| `clicks` | `INTEGER` | NO | Click-throughs (Default: 0) |
| `chunks` | `INTEGER` | NO | SMS chunks used (Default: 0) |
| `usuarios_unicos` | `INTEGER` | NO | Distinct recipients (Default: 0) |
| `abiertos` | `INTEGER` | YES | Opens (Email only) |
| `rebotes` | `INTEGER` | YES | Bounces (Email only) |
| `bloqueados` | `INTEGER` | YES | Blocked (Email only) |
| `spam` | `INTEGER` | YES | Spam complaints (Email only) |
| `desuscritos` | `INTEGER` | YES | Unsubscribes (Email only) |
| `conversiones` | `INTEGER` | YES | Conversions (In-App/Web only) |
| `ctr` | `NUMERIC(6,2)` | YES | Calculated: clicks/enviados*100 |
| `tasa_entrega` | `NUMERIC(6,2)` | YES | Calculated: entregados/enviados*100 |
| `open_rate` | `NUMERIC(6,2)` | YES | Calculated: abiertos/entregados*100 |
| `conversion_rate` | `NUMERIC(6,2)` | YES | Calculated: conversiones/clicks*100 |

**Indexes:**
- `idx_toques_daily_tenant_date` on `(tenant_id, date)`
- `idx_toques_daily_canal` on `(tenant_id, canal)`
- `idx_toques_daily_project` on `(tenant_id, proyecto_cuenta)`

**Primary Key:** `id`
**Unique:** `(tenant_id, date, canal, proyecto_cuenta)`
**RLS Policy:** `tenant_id = current_setting('app.current_tenant')`

---

#### `campaigns` — Dimension table (campaign master data)

**Source:** Campaign API via n8n (currently: `campanas_summary.csv`, 72 rows)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | `SERIAL` | NO | Internal PK |
| `tenant_id` | `VARCHAR(50)` | NO | Tenant isolation key |
| `campana_id` | `VARCHAR(100)` | NO | Source campaign ID |
| `campana_nombre` | `VARCHAR(255)` | NO | Campaign display name |
| `canal` | `VARCHAR(30)` | NO | Channel |
| `proyecto_cuenta` | `VARCHAR(100)` | NO | Project/account |
| `tipo_campana` | `VARCHAR(50)` | YES | Campaign type |
| `total_enviados` | `INTEGER` | NO | Lifetime sends (Default: 0) |
| `total_entregados` | `INTEGER` | NO | Lifetime delivered (Default: 0) |
| `total_clicks` | `INTEGER` | NO | Lifetime clicks (Default: 0) |
| `total_chunks` | `INTEGER` | NO | Lifetime chunks (Default: 0) |
| `fecha_inicio` | `DATE` | YES | Campaign start date |
| `fecha_fin` | `DATE` | YES | Campaign end date |
| `total_abiertos` | `INTEGER` | YES | Opens (Email) |
| `total_rebotes` | `INTEGER` | YES | Bounces (Email) |
| `total_bloqueados` | `INTEGER` | YES | Blocked (Email) |
| `total_spam` | `INTEGER` | YES | Spam (Email) |
| `total_desuscritos` | `INTEGER` | YES | Unsubscribes (Email) |
| `total_conversiones` | `INTEGER` | YES | Conversions (In-App) |
| `ctr` | `NUMERIC(6,2)` | YES | CTR % |
| `tasa_entrega` | `NUMERIC(6,2)` | YES | Delivery rate % |
| `open_rate` | `NUMERIC(6,2)` | YES | Open rate % (Email) |
| `conversion_rate` | `NUMERIC(6,2)` | YES | Conversion rate % (In-App) |

**Primary Key:** `id`
**Unique:** `(tenant_id, campana_id)`
**RLS Policy:** `tenant_id = current_setting('app.current_tenant')`

---

#### `toques_heatmap` — Pre-aggregated (day-of-week x hour)

**Source:** Pre-computed from toques_daily (currently: `toques_heatmap.csv`, 513 rows)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | `SERIAL` | NO | Internal PK |
| `tenant_id` | `VARCHAR(50)` | NO | Tenant isolation key |
| `canal` | `VARCHAR(30)` | NO | Channel |
| `dia_semana` | `VARCHAR(12)` | NO | Lunes, Martes, ... Domingo |
| `hora` | `SMALLINT` | NO | 0-23 |
| `enviados` | `INTEGER` | NO | Sum of sends for this slot |
| `clicks` | `INTEGER` | NO | Sum of clicks |
| `abiertos` | `INTEGER` | YES | Opens (Email) |
| `conversiones` | `INTEGER` | YES | Conversions (In-App) |
| `ctr` | `NUMERIC(6,2)` | YES | CTR % |
| `dia_orden` | `SMALLINT` | NO | Sort order 1-7 (Mon=1) |

**Primary Key:** `id`
**Unique:** `(tenant_id, canal, dia_semana, hora)`
**RLS Policy:** `tenant_id = current_setting('app.current_tenant')`

---

#### `toques_usuario` — Pre-aggregated per-user campaign metrics

**Source:** Derived from toques (currently: `toques_usuario.csv`, 675,389 rows)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | `SERIAL` | NO | Internal PK |
| `tenant_id` | `VARCHAR(50)` | NO | Tenant isolation key |
| `telefono` | `VARCHAR(50)` | NO | Phone number (hashed in production) |
| `canal` | `VARCHAR(30)` | NO | Channel |
| `proyecto_cuenta` | `VARCHAR(100)` | NO | Project/account |
| `total_toques` | `INTEGER` | NO | Total touches received |
| `total_clicks` | `INTEGER` | NO | Total clicks |
| `primer_toque` | `DATE` | YES | First touch date |
| `ultimo_toque` | `DATE` | YES | Last touch date |
| `dias_activos` | `INTEGER` | NO | Days with activity |

**Indexes:**
- `idx_toques_usuario_tenant` on `(tenant_id)`
- `idx_toques_usuario_phone` on `(tenant_id, telefono)`
- `idx_toques_usuario_volume` on `(tenant_id, total_toques DESC)`

**Primary Key:** `id`
**Unique:** `(tenant_id, telefono, canal, proyecto_cuenta)`
**RLS Policy:** `tenant_id = current_setting('app.current_tenant')`

---

### 2.3 Application Domain

#### `saved_queries` — Shared AI query results (tenant-wide)

**Source:** Platform application (replaces filesystem `StorageService`)

> **Sharing model:** All saved queries are **shared across the entire tenant** by default. Every user within a project/organization sees the same queries, dashboards, and visualizations. There is no private/published toggle — RLS isolates tenants, but within a tenant everything is collaborative. `created_by` tracks authorship for attribution, not access control.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | `SERIAL` | NO | Internal PK |
| `tenant_id` | `VARCHAR(50)` | NO | Tenant isolation key |
| `name` | `VARCHAR(255)` | NO | User-defined query name |
| `query_text` | `TEXT` | NO | Original natural language question |
| `ai_function` | `VARCHAR(50)` | YES | Pre-built function used (e.g., "summary") |
| `generated_sql` | `TEXT` | YES | SQL generated by AI fallback (NULL if pre-built) |
| `result_data` | `JSONB` | NO | Query result as JSON (records format) |
| `result_columns` | `JSONB` | NO | Column names + types array |
| `result_row_count` | `INTEGER` | NO | Number of rows returned |
| `visualizations` | `JSONB` | NO | Array of visualization configs (Default: '[]') |
| `tags` | `TEXT[]` | YES | Array of user tags |
| `is_favorite` | `BOOLEAN` | NO | Starred by user (Default: false) |
| `is_archived` | `BOOLEAN` | NO | Soft-deleted (Default: false) |
| `created_by` | `VARCHAR(100)` | YES | User who created (attribution only, not access control) |
| `created_at` | `TIMESTAMPTZ` | NO | Creation timestamp (Default: now()) |
| `updated_at` | `TIMESTAMPTZ` | NO | Last update (Default: now()) |
| `updated_by` | `VARCHAR(100)` | YES | User who last modified |
| `last_run_at` | `TIMESTAMPTZ` | YES | Last time query was re-executed |

**`visualizations` JSONB structure:**
```json
[
  {
    "id": "viz_1",
    "name": "Grafico 1",
    "type": "bar",
    "config": {
      "x_col": "date",
      "y_col": "count",
      "group_col": null,
      "color_col": null,
      "orientation": "v",
      "title": ""
    },
    "is_default": true,
    "created_at": "2026-01-15T10:00:00Z"
  }
]
```

**Indexes:**
- `idx_saved_queries_tenant` on `(tenant_id)`
- `idx_saved_queries_favorite` on `(tenant_id, is_favorite) WHERE is_archived = false`
- `idx_saved_queries_search` on `(tenant_id)` + GIN index on `name` for text search

**Primary Key:** `id`
**RLS Policy:** `tenant_id = current_setting('app.current_tenant')`

---

#### `dashboards` — Shared dashboards (tenant-wide)

> **Sharing model:** Same as `saved_queries` — all dashboards are **shared across the entire tenant**. When one user creates or edits a dashboard, all other users in the same project/organization see it immediately. `created_by` / `updated_by` track authorship, not access.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | `SERIAL` | NO | Internal PK |
| `tenant_id` | `VARCHAR(50)` | NO | Tenant isolation key |
| `name` | `VARCHAR(255)` | NO | Dashboard display name |
| `description` | `TEXT` | YES | Optional description |
| `layout` | `JSONB` | NO | Widget grid layout (Default: '[]') |
| `filters` | `JSONB` | YES | Dashboard-level filter config |
| `tags` | `TEXT[]` | YES | User tags |
| `is_favorite` | `BOOLEAN` | NO | Starred (Default: false) |
| `is_archived` | `BOOLEAN` | NO | Soft-deleted (Default: false) |
| `is_default` | `BOOLEAN` | NO | Auto-created primary dashboard (Default: false) |
| `auto_refresh_seconds` | `INTEGER` | YES | Auto-refresh interval (NULL = off) |
| `created_by` | `VARCHAR(100)` | YES | User who created (attribution only) |
| `updated_by` | `VARCHAR(100)` | YES | User who last modified |
| `created_at` | `TIMESTAMPTZ` | NO | Default: now() |
| `updated_at` | `TIMESTAMPTZ` | NO | Default: now() |

**`layout` JSONB structure:**
```json
[
  {
    "widget_id": "w_1",
    "query_id": 42,
    "visualization_id": "viz_1",
    "x": 0, "y": 0,
    "w": 3, "h": 2,
    "title_override": null
  },
  {
    "widget_id": "w_2",
    "type": "text",
    "content": "## Metricas Principales",
    "x": 0, "y": 2,
    "w": 6, "h": 1
  }
]
```

**Primary Key:** `id`
**RLS Policy:** `tenant_id = current_setting('app.current_tenant')`

---

#### `sync_state` — ETL tracking

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | `SERIAL` | NO | Internal PK |
| `tenant_id` | `VARCHAR(50)` | NO | Tenant being synced |
| `entity` | `VARCHAR(50)` | NO | messages, contacts, campaigns, etc. |
| `last_cursor` | `TEXT` | YES | API pagination cursor |
| `last_sync_at` | `TIMESTAMPTZ` | YES | Last successful sync |
| `records_synced` | `INTEGER` | YES | Records in last batch |
| `status` | `VARCHAR(20)` | NO | success, failed, running |
| `error_message` | `TEXT` | YES | Error details if failed |

**Primary Key:** `id`
**Unique:** `(tenant_id, entity)`

---

## 3. Dimension Definitions

Every dimension the platform can filter or group by:

| Dimension | Column(s) | Tables Available In | Filter Type | Example Values |
|-----------|-----------|-------------------|-------------|----------------|
| **Time (date)** | `date` | messages, daily_stats, toques_daily | Date range picker | 2025-01-01 to 2025-01-31 |
| **Time (hour)** | `hour` | messages, toques_heatmap | None (used in charts) | 0-23 |
| **Day of Week** | `day_of_week` / `dia_semana` | messages, toques_heatmap | None (used in charts) | Monday...Sunday / Lunes...Domingo |
| **Channel (conversations)** | `direction` | messages | Multiselect dropdown | Inbound, Bot, Agent, Outbound |
| **Channel (campaigns)** | `canal` | toques_daily, campaigns, toques_heatmap, toques_usuario | Multiselect dropdown | SMS, WhatsApp, Email, Push, In App/Web |
| **Project/Account** | `proyecto_cuenta` | toques_daily, campaigns, toques_usuario | Single-select dropdown | "Proyecto Alpha", "Cuenta Beta" |
| **Entity (tenant sub-unit)** | `entity` (→ `tenant_id`) | messages, contacts | Single-select dropdown | "Utrahuilca", "Vidasol", "Coovimag" |
| **Contact** | `contact_id` / `contact_name` | messages, contacts | Search input | Contact name or ID |
| **Phone** | `telefono` | toques_usuario | Search input | "+573001234567" |
| **Agent** | `agent_id` | messages, agents | Dropdown | "agent_001", "agent_002" |
| **Intent** | `intent` | messages | Dropdown | "Default Fallback Intent", "Privacy Accepted" |
| **Fallback** | `is_fallback` | messages | Toggle | true / false |
| **Campaign** | `campana_id` / `campana_nombre` | campaigns, toques_daily | Dropdown / table filter | "Campaña Navidad 2025" |
| **Campaign Type** | `tipo_campana` | campaigns | Dropdown | "Promocional", "Informativa" |
| **Send Type** | `send_type` | messages | Multiselect | input, dialogflow, operator |
| **Content Type** | `content_type` | messages | Multiselect | text, interactive, event |

---

## 4. Metric Definitions (Formulas)

### 4.1 Conversation Metrics

| Metric | SQL Formula | Unit | Target |
|--------|-----------|------|--------|
| **Total Messages** | `COUNT(*)` from messages | count | — |
| **Unique Contacts** | `COUNT(DISTINCT contact_id)` from messages | count | — |
| **Active Agents** | `COUNT(DISTINCT agent_id) WHERE agent_id IS NOT NULL` | count | — |
| **Total Conversations** | `COUNT(DISTINCT conversation_id)` from messages | count | — |
| **Fallback Rate** | `COUNT(*) FILTER(WHERE is_fallback) / COUNT(*) * 100` | % | < 15% |
| **Bot Resolution Rate** | `COUNT(*) FILTER(WHERE direction='Bot') / COUNT(*) FILTER(WHERE direction='Inbound') * 100` | % | > 70% |
| **Avg Wait Time** | `AVG(wait_time_seconds) FILTER(WHERE wait_time_seconds > 0)` | seconds | < 60s |
| **Avg Handle Time** | `AVG(handle_time_seconds) FILTER(WHERE handle_time_seconds > 0)` | seconds | < 300s |
| **Messages by Direction** | `COUNT(*) GROUP BY direction` | count | — |
| **Messages by Hour** | `COUNT(*) GROUP BY hour` | count | — |
| **Messages Over Time** | `COUNT(*) GROUP BY date` | count | — |
| **Messages by Day of Week** | `COUNT(*) GROUP BY day_of_week` | count | — |
| **Top N Contacts** | `COUNT(*) GROUP BY contact_name ORDER BY count DESC LIMIT N` | count | — |
| **Intent Distribution** | `COUNT(*) GROUP BY intent ORDER BY count DESC LIMIT N` | count | — |
| **Agent Performance** | `COUNT(*), COUNT(DISTINCT conversation_id) GROUP BY agent_id` | count | — |
| **High-Message Customers** | `COUNT(*) GROUP BY contact_id, period HAVING COUNT(*) > threshold` | count | — |

### 4.2 Campaign Metrics

| Metric | SQL Formula | Unit | Channel |
|--------|-----------|------|---------|
| **Total Enviados** | `SUM(enviados)` from toques_daily | count | All |
| **Total Clicks** | `SUM(clicks)` from toques_daily | count | All |
| **Total Chunks** | `SUM(chunks)` from toques_daily | count | SMS |
| **CTR** | `SUM(clicks) / NULLIF(SUM(enviados), 0) * 100` | % | All |
| **Delivery Rate** | `SUM(entregados) / NULLIF(SUM(enviados), 0) * 100` | % | All |
| **Open Rate** | `SUM(abiertos) / NULLIF(SUM(entregados), 0) * 100` | % | Email |
| **Bounce Rate** | `SUM(rebotes) / NULLIF(SUM(enviados), 0) * 100` | % | Email |
| **Spam Rate** | `SUM(spam) / NULLIF(SUM(entregados), 0) * 100` | % | Email |
| **Unsubscribe Rate** | `SUM(desuscritos) / NULLIF(SUM(entregados), 0) * 100` | % | Email |
| **Conversion Rate** | `SUM(conversiones) / NULLIF(SUM(clicks), 0) * 100` | % | In-App/Web |
| **Active Campaigns** | `COUNT(*) FROM campaigns WHERE fecha_fin >= CURRENT_DATE` | count | All |
| **Unique Users** | `SUM(usuarios_unicos)` from toques_daily | count | All |

---

## 5. Query Catalog

Every query the application executes, organized by the page that uses it.

### 5.1 Home Page (2 queries)

| # | Service Method | SQL Equivalent | Returns |
|---|---------------|----------------|---------|
| H1 | `get_favorite_queries()` | `SELECT * FROM saved_queries WHERE is_favorite AND NOT is_archived ORDER BY updated_at DESC LIMIT 10` | ~10 rows |
| H2 | `get_favorite_dashboards()` | `SELECT * FROM dashboards WHERE is_favorite AND NOT is_archived ORDER BY updated_at DESC LIMIT 10` | ~10 rows |

### 5.2 Query Page — AI Agent Pre-Built Functions (13 queries)

| # | Function Name | Source Table | Query Pattern | Default Chart |
|---|--------------|-------------|---------------|---------------|
| Q1 | `summary` | messages | `SELECT COUNT(*), COUNT(DISTINCT contact_id), COUNT(DISTINCT conversation_id), COUNT(DISTINCT agent_id)` + fallback rate | table |
| Q2 | `fallback_rate` | messages | `SELECT COUNT(*) FILTER(WHERE is_fallback), COUNT(*), ratio` | table/KPI |
| Q3 | `messages_by_direction` | messages | `SELECT direction, COUNT(*) GROUP BY direction` | pie |
| Q4 | `messages_by_hour` | messages | `SELECT hour, COUNT(*) GROUP BY hour ORDER BY hour` | bar |
| Q5 | `messages_over_time` | messages | `SELECT date, COUNT(*) GROUP BY date ORDER BY date` | line |
| Q6 | `messages_by_day_of_week` | messages | `SELECT day_of_week, COUNT(*) GROUP BY day_of_week` | bar |
| Q7 | `top_contacts` | messages | `SELECT contact_name, COUNT(*) GROUP BY contact_name ORDER BY count DESC LIMIT 10` | horizontal_bar |
| Q8 | `intent_distribution` | messages | `SELECT intent, COUNT(*) GROUP BY intent ORDER BY count DESC LIMIT 10` | horizontal_bar |
| Q9 | `agent_performance` | messages | `SELECT agent_id, COUNT(*), COUNT(DISTINCT conversation_id) WHERE agent_id IS NOT NULL GROUP BY agent_id` | bar |
| Q10 | `entity_comparison` | messages | `SELECT entity, COUNT(*) GROUP BY entity ORDER BY count DESC LIMIT 15` | horizontal_bar |
| Q11 | `high_messages_day` | messages | `SELECT contact_id, contact_name, date, COUNT(*) GROUP BY ... HAVING COUNT(*) > 4` | table |
| Q12 | `high_messages_week` | messages | Same as Q11 with `DATE_TRUNC('week', date)` | table |
| Q13 | `high_messages_month` | messages | Same as Q11 with `DATE_TRUNC('month', date)` | table |

### 5.3 Query Page — SQL Fallback (dynamic)

| # | Pattern | SQL Generation | Guardrails |
|---|---------|---------------|------------|
| Q14 | Ad-hoc natural language | Claude generates SELECT query | SELECT only, allowed tables whitelist, auto-inject `tenant_id`, LIMIT 1000, 10s timeout |

### 5.4 Dashboard Page — Primary Dashboard (11 queries)

| # | Service Method | Source | Filters Applied | Returns |
|---|---------------|--------|-----------------|---------|
| D1 | `get_kpis()` | toques_daily | canal, proyecto_cuenta | 5 KPI values |
| D2 | `get_sends_vs_chunks()` | toques_daily | canal, proyecto_cuenta | ~30-365 rows (date series) |
| D3 | `get_sends_clicks_ctr()` | toques_daily | canal, proyecto_cuenta | ~30-365 rows (date series) |
| D4 | `get_campaigns_by_volume()` | campaigns | canal, proyecto_cuenta | 10 rows |
| D5 | `get_campaigns_by_ctr()` | campaigns | canal, proyecto_cuenta | 10 rows |
| D6 | `get_heatmap_data()` | toques_heatmap | canal | 168 rows (7x24) |
| D7 | `get_campaign_details()` | campaigns | canal, proyecto_cuenta | ~50-100 rows |
| D8 | `get_active_campaigns_count()` | campaigns | canal, proyecto_cuenta | 1 value |

### 5.5 Dashboard Page — Email Tab (5 queries)

| # | Service Method | Source | Returns |
|---|---------------|--------|---------|
| E1 | `get_email_kpis()` | toques_daily WHERE canal='Email' | 11 KPI values |
| E2 | `get_email_engagement_trend()` | toques_daily WHERE canal='Email' | date series |
| E3 | `get_email_error_breakdown()` | toques_daily WHERE canal='Email' | 4 rows (rebotes, bloqueados, spam, desuscritos) |
| E4 | `get_email_campaigns_by_engagement()` | campaigns WHERE canal='Email' | 10 rows |
| E5 | `get_email_campaign_details()` | campaigns WHERE canal='Email' | ~20-50 rows |

### 5.6 Dashboard Page — In-App/Web Tab (5 queries)

| # | Service Method | Source | Returns |
|---|---------------|--------|---------|
| I1 | `get_inapp_kpis()` | toques_daily WHERE canal='In App/Web' | 6 KPI values |
| I2 | `get_inapp_engagement_trend()` | toques_daily WHERE canal='In App/Web' | date series |
| I3 | `get_inapp_conversion_funnel()` | toques_daily WHERE canal='In App/Web' | 3 rows |
| I4 | `get_inapp_campaigns_by_conversion()` | campaigns WHERE canal='In App/Web' | 10 rows |
| I5 | `get_inapp_campaign_details()` | campaigns WHERE canal='In App/Web' | ~10-30 rows |

### 5.7 Dashboard Page — Users Tab (1 query)

| # | Service Method | Source | Returns |
|---|---------------|--------|---------|
| U1 | `get_users_high_volume()` | toques_usuario | ~100 rows (threshold-filtered) |

### 5.8 Application CRUD (8 queries)

| # | Operation | Table | Description |
|---|-----------|-------|-------------|
| A1 | `list_queries()` | saved_queries | Paginated list, filtered by tenant/favorite/tags/archived |
| A2 | `get_query(id)` | saved_queries | Single query with all data |
| A3 | `save_query()` | saved_queries | INSERT or UPDATE |
| A4 | `archive_query(id)` | saved_queries | SET is_archived = true |
| A5 | `list_dashboards()` | dashboards | Paginated list |
| A6 | `get_dashboard(id)` | dashboards + saved_queries | Dashboard + all widget query data |
| A7 | `save_dashboard()` | dashboards | INSERT or UPDATE (layout JSONB) |
| A8 | `archive_dashboard(id)` | dashboards | SET is_archived = true |

### 5.9 Utility Queries (4 queries)

| # | Method | Source | Purpose |
|---|--------|--------|---------|
| U1 | `get_entities()` | messages | Populate tenant selector |
| U2 | `get_channels()` | toques_daily | Populate channel filter |
| U3 | `get_projects()` | toques_daily | Populate project filter |
| U4 | `get_date_range()` | toques_daily / messages | Display date range, validate filter inputs |

**Total: ~49 distinct queries** across all pages.

---

## 6. Data Quality Rules

### 6.1 Known Issues in Current Data

| Issue | Table | Column | Impact | Fix |
|-------|-------|--------|--------|-----|
| Concatenated strings | daily_stats | fallback_count | Cannot aggregate | Re-derive from messages: `COUNT(*) WHERE is_fallback` |
| Garbled characters | contacts | contact_name | Display issues | UTF-8 normalize in staging model |
| Naming inconsistency | messages vs toques | entity vs proyecto_cuenta | Different dimension names for similar concept | Map in staging: `entity` for conversations, `proyecto_cuenta` for campaigns; both resolve to `tenant_id` |
| String booleans | messages | is_fallback | "Yes"/"No" instead of true/false | Cast in staging: `LOWER(is_fallback) = 'yes'` → BOOLEAN |
| NULL agent_ids | messages | agent_id | Expected for bot messages | No fix needed; filter in queries with `WHERE agent_id IS NOT NULL` |

### 6.2 Validation Rules (dbt tests)

| Test | Table | Rule | Severity |
|------|-------|------|----------|
| `not_null` | All | `tenant_id IS NOT NULL` | ERROR |
| `not_null` | messages | `message_id, timestamp, direction IS NOT NULL` | ERROR |
| `not_null` | toques_daily | `date, canal, proyecto_cuenta IS NOT NULL` | ERROR |
| `unique` | messages | `(tenant_id, message_id)` | ERROR |
| `unique` | toques_daily | `(tenant_id, date, canal, proyecto_cuenta)` | ERROR |
| `accepted_values` | messages.direction | Inbound, Bot, Agent, Outbound, System | WARN |
| `accepted_values` | toques_daily.canal | SMS, WhatsApp, Email, Push, In App/Web | WARN |
| `relationships` | messages.contact_id | References contacts.contact_id | WARN |
| `positive_values` | toques_daily | enviados, entregados, clicks >= 0 | ERROR |
| `range_check` | toques_daily.ctr | 0 <= ctr <= 100 | WARN |
| `range_check` | messages.hour | 0 <= hour <= 23 | ERROR |

### 6.3 Deduplication

| Table | Dedup Key | Strategy |
|-------|-----------|----------|
| messages | `(tenant_id, message_id)` | INSERT ON CONFLICT DO NOTHING (immutable) |
| contacts | `(tenant_id, contact_id)` | UPSERT — update totals, keep latest name |
| agents | `(tenant_id, agent_id)` | UPSERT — update aggregates |
| toques_daily | `(tenant_id, date, canal, proyecto_cuenta)` | UPSERT — replace with latest values |
| campaigns | `(tenant_id, campana_id)` | UPSERT — update stats and dates |

---

## 7. dbt Layer Design: RAW → STAGING → MARTS

### 7.1 Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  RAW Schema │     │ STAGING Schema   │     │  MARTS Schema   │
│             │     │  (views)         │     │  (tables)       │
│  raw_       │────▶│  stg_            │────▶│  (final names)  │
│  messages   │     │  messages        │     │  messages       │
│  raw_       │     │  stg_            │     │  contacts       │
│  toques     │     │  toques_daily    │     │  toques_daily   │
│  raw_       │     │  stg_            │     │  campaigns      │
│  campaigns  │     │  campaigns       │     │  daily_stats    │
│  ...        │     │  ...             │     │  ...            │
└─────────────┘     └──────────────────┘     └─────────────────┘
    n8n writes          dbt transforms           App reads
    JSONB blobs         cleans + types           via SQLAlchemy
```

### 7.2 RAW Tables (n8n writes here)

One table per API entity group. All store raw JSON in a JSONB column.

```sql
-- raw_messages: n8n writes WhatsApp API responses here
CREATE TABLE raw.raw_messages (
    id          SERIAL PRIMARY KEY,
    tenant_id   VARCHAR(50) NOT NULL,
    loaded_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_data JSONB NOT NULL
);

-- raw_toques: n8n writes campaign API responses here
CREATE TABLE raw.raw_toques (
    id          SERIAL PRIMARY KEY,
    tenant_id   VARCHAR(50) NOT NULL,
    loaded_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_data JSONB NOT NULL
);

-- raw_campaigns: n8n writes campaign master data here
CREATE TABLE raw.raw_campaigns (
    id          SERIAL PRIMARY KEY,
    tenant_id   VARCHAR(50) NOT NULL,
    loaded_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_data JSONB NOT NULL
);

-- raw_contacts: n8n writes user/contact data here
CREATE TABLE raw.raw_contacts (
    id          SERIAL PRIMARY KEY,
    tenant_id   VARCHAR(50) NOT NULL,
    loaded_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_data JSONB NOT NULL
);
```

### 7.3 STAGING Models (dbt views)

Materialized as **views**. Purpose: extract typed columns from JSONB, clean, normalize, deduplicate.

**`stg_messages.sql`** — Extract from raw_messages:
- Cast timestamp fields to TIMESTAMPTZ
- Extract date, hour, day_of_week from timestamp
- Normalize `is_fallback` from "Yes"/"No" to BOOLEAN
- Normalize `direction` values (trim, consistent casing)
- UTF-8 clean `contact_name`
- Deduplicate on `(tenant_id, message_id)` using `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY loaded_at DESC)`

**`stg_toques_daily.sql`** — Extract from raw_toques:
- Cast date, numeric columns
- Compute `ctr`, `tasa_entrega`, `open_rate`, `conversion_rate` with NULLIF guards
- Validate non-negative values

**`stg_campaigns.sql`** — Extract from raw_campaigns:
- Cast dates, numerics
- Deduplicate on `(tenant_id, campana_id)`

**`stg_contacts.sql`** — Extract from raw_contacts or derive from stg_messages:
- Aggregate `total_messages`, `first_contact`, `last_contact` from messages
- UTF-8 clean names

### 7.4 MARTS Models (dbt tables)

Materialized as **tables** (for query performance). These are the tables the app queries.

| Mart Model | Source | Materialization | Grain | Description |
|-----------|--------|----------------|-------|-------------|
| `messages` | stg_messages | incremental | 1 row per message | Full message fact table |
| `contacts` | stg_contacts | table | 1 row per contact per tenant | Contact dimension with aggregates |
| `agents` | stg_messages (aggregated) | table | 1 row per agent per tenant | Agent performance dimension |
| `daily_stats` | stg_messages (aggregated) | table | 1 row per tenant per date | Daily conversation summary |
| `toques_daily` | stg_toques_daily | incremental | 1 row per tenant/date/canal/project | Daily campaign metrics |
| `campaigns` | stg_campaigns | table | 1 row per campaign per tenant | Campaign dimension |
| `toques_heatmap` | stg_toques_daily (aggregated) | table | 1 row per tenant/canal/day/hour | Pre-computed heatmap data |
| `toques_usuario` | stg_toques_daily (aggregated) | table | 1 row per user/canal/project | User-level campaign aggregates |

### 7.5 dbt Project Structure

```
dbt/
├── dbt_project.yml
├── profiles.yml
├── packages.yml         # dbt-utils
└── models/
    ├── sources.yml      # raw schema source definitions
    ├── staging/
    │   ├── _staging.yml        # schema tests for staging models
    │   ├── stg_messages.sql
    │   ├── stg_toques_daily.sql
    │   ├── stg_campaigns.sql
    │   └── stg_contacts.sql
    └── marts/
        ├── _marts.yml          # schema tests for mart models
        ├── messages.sql
        ├── contacts.sql
        ├── agents.sql
        ├── daily_stats.sql
        ├── toques_daily.sql
        ├── campaigns.sql
        ├── toques_heatmap.sql
        └── toques_usuario.sql
```

---

## 8. Row-Level Security (RLS)

### Policy Setup

```sql
-- Enable RLS on all tenant-scoped tables
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE toques_daily ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE toques_heatmap ENABLE ROW LEVEL SECURITY;
ALTER TABLE toques_usuario ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_queries ENABLE ROW LEVEL SECURITY;
ALTER TABLE dashboards ENABLE ROW LEVEL SECURITY;

-- Create policy (same for each table)
CREATE POLICY tenant_isolation ON messages
    USING (tenant_id = current_setting('app.current_tenant', true));

-- Repeat for all tables above
```

### Context Setting (per request)

The Flask middleware sets the tenant context on every request:

```sql
-- Called by middleware before any query
SET LOCAL app.current_tenant = 'tenant_xyz';
```

This ensures that even if application code forgets a WHERE clause, RLS blocks cross-tenant data access.

---

## 9. Seed Data Migration

### Strategy

The seed script reads all CSVs from the demo `data/processed/` directory and inserts directly into the MARTS tables (bypassing RAW/STAGING for initial load).

### Tenant ID Derivation

| CSV Source | Tenant Column | Mapping |
|-----------|---------------|---------|
| messages.csv | `entity` | Use entity value as tenant_id |
| contacts.csv | `entity` | Use entity value as tenant_id |
| agents.csv | (none) | Assign a default tenant_id per entity derived from messages |
| daily_stats.csv | (none) | Assign default "demo" tenant_id |
| toques_daily.csv | `proyecto_cuenta` | Use proyecto_cuenta as tenant_id |
| campanas_summary.csv | `proyecto_cuenta` | Use proyecto_cuenta as tenant_id |
| toques_usuario.csv | `proyecto_cuenta` | Use proyecto_cuenta as tenant_id |
| toques_heatmap.csv | `canal` | Assign default "demo" tenant_id |

**Note:** In production, `tenant_id` comes from the JWT claim (= indigitall's `project_id`). The seed data maps `entity` and `proyecto_cuenta` to serve as demo tenant IDs.

---

## 10. Data Gaps + Future Tables

### 10.1 What Exists Now vs. What's Planned

| Data Entity | Current State | Production Source | Status |
|-------------|--------------|-------------------|--------|
| Messages (WhatsApp) | CSV, 50K rows | WhatsApp Business API | Ready to build |
| Contacts | CSV, 623 rows | Derived from messages + Users API | Ready to build |
| Agents | CSV, 13 rows | Derived from messages | Ready to build |
| Daily Stats | CSV, 29 rows | dbt aggregation from messages | Ready to build |
| Toques Daily | CSV, 1K rows | Campaign API | Ready to build |
| Campaigns | CSV, 72 rows | Campaign API | Ready to build |
| Toques Heatmap | CSV, 513 rows | dbt aggregation from toques | Ready to build |
| Toques Usuario | CSV, 675K rows | dbt aggregation from toques | Ready to build |
| Events | Defined in doc 06 | Events API (TBD) | BLOCKED — waiting for D14 |
| Transactions | Defined in doc 06 | Transactions API (TBD) | BLOCKED — waiting for D14 |
| Segments | Mentioned in doc 06 | Segments API (TBD) | FUTURE |

### 10.2 Future Tables (When API Access Arrives)

**`events`** — Will unify all engagement events (opens, clicks, page views) from the Events API into a single fact table matching the `fct_activities` schema from doc 06.

**`transactions`** — Financial events, stored as activities with `activity_category = 'transaction'`. Only needed if indigitall provides financial data.

**`segments`** — User segments defined in indigitall's platform. Low priority, synced via full-refresh.

### 10.3 Schema Evolution Strategy

When D14 (Sample API Responses) arrives from indigitall:
1. Compare actual API field names with doc 06 mappings
2. Create/update RAW tables for new entities
3. Create staging models to extract + type the JSONB
4. Create or extend mart models
5. Update service layer queries
6. No schema changes needed for `saved_queries` or `dashboards` — they store query results as JSONB and are API-agnostic

---

## 11. Estimated Data Volumes (Production, Per Tenant)

| Table | Est. Rows/Month | Est. Rows/Year | Growth Rate |
|-------|----------------|----------------|-------------|
| messages | 10,000 - 50,000 | 120K - 600K | Linear with traffic |
| contacts | 500 - 2,000 (cumulative) | 2K - 10K | Decelerating |
| agents | 10 - 50 (cumulative) | 50 | Near-static |
| daily_stats | 30 | 365 | Fixed (1/day) |
| toques_daily | 150 (5 channels x 30 days) | 1,800 | Fixed |
| campaigns | 20 - 50 | 200 - 600 | Linear with activity |
| toques_heatmap | 840 (5 channels x 7 x 24) | 840 | Fixed (rebuilt) |
| toques_usuario | 5,000 - 50,000 | 50K - 500K | Linear with campaigns |
| saved_queries | 10 - 50 | 100 - 500 | Linear with usage |
| dashboards | 2 - 10 | 10 - 50 | Slow growth |

**Total per tenant:** ~200K - 1.2M rows/year
**For 10 tenants:** ~2M - 12M rows/year

PostgreSQL on a 4-8GB VPS handles this comfortably with proper indexing.
