# Modelo de Datos — inDigitall BI Platform

## Arquitectura General

```
Indigitall API (am1.api.indigitall.com)
    |  ServerKey auth
    v
Python Extractors (scripts/extractors/)
    |  GET endpoints → almacena respuestas completas
    v
raw.* (PostgreSQL - JSONB)
    |  Transform Bridge (scripts/transform_bridge.py)
    v
public.* (PostgreSQL - tablas estructuradas)
    |  dbt (staging → marts)
    v
Plotly Dash App (dashboards BI)
```

---

## Esquema RAW (raw.*)

Tablas JSONB que almacenan respuestas crudas de la API. Nunca se borran datos — solo se agregan (append-only).

| Tabla | Fuente API | Descripcion |
|---|---|---|
| `raw.raw_contacts_api` | `/v1/chat/contacts` | Contactos de WhatsApp/webchat |
| `raw.raw_push_stats` | `/v1/application/{id}/dateStats`, `/pushHeatmap` | Estadisticas push por dia y heatmap |
| `raw.raw_chat_stats` | `/v1/chat/history/csv`, `/agent/conversations`, `/channel`, etc. | Mensajes, conversaciones, canales |
| `raw.raw_campaigns_api` | `/v1/campaign` | Campanas y sus metricas |
| `raw.raw_applications` | `/v1/application` | Metadata de aplicaciones |
| `raw.raw_sms_stats` | Endpoints SMS | Estadisticas SMS |
| `raw.raw_email_stats` | Endpoints Email | Estadisticas Email |
| `raw.raw_inapp_stats` | Endpoints In-App | Estadisticas In-App |
| `raw.extraction_log` | (metadata) | Log de llamadas API (status, duracion, errores) |

### Estructura comun de tablas raw

```sql
id              SERIAL PRIMARY KEY
application_id  VARCHAR(100)      -- ID de la app en Indigitall (ej: "100274")
tenant_id       VARCHAR(50)       -- Tenant (ej: "visionamos")
endpoint        VARCHAR(200)      -- Endpoint API de origen
loaded_at       TIMESTAMPTZ       -- Momento de carga
date_from       DATE              -- Rango consulta (inicio)
date_to         DATE              -- Rango consulta (fin)
source_data     JSONB NOT NULL    -- Respuesta completa de la API
```

---

## Esquema PUBLIC (public.*)

### Dominio: Conversaciones (Chat/WhatsApp)

#### `messages` — Tabla de hechos: mensajes individuales

Fuente: `/v1/chat/history/csv` via transform_bridge

| Columna | Tipo | Descripcion |
|---|---|---|
| `id` | SERIAL PK | |
| `tenant_id` | TEXT | Tenant (RLS) |
| `message_id` | VARCHAR(100) | ID unico del mensaje en Indigitall |
| `timestamp` | TIMESTAMPTZ | Fecha/hora exacta del mensaje |
| `date` | DATE | Fecha (para joins con daily_stats) |
| `hour` | SMALLINT | Hora (0-23) |
| `day_of_week` | VARCHAR(10) | Dia de la semana (Monday, Tuesday, etc.) |
| `send_type` | VARCHAR(30) | Tipo: `input`, `operator`, `dialogflow`, `agent_notification` |
| `direction` | VARCHAR(20) | Direccion derivada: `Inbound`, `Agent`, `Bot`, `System`, `Outbound` |
| `content_type` | VARCHAR(30) | Tipo contenido: `text`, `quickReplyEvent`, `image`, `interactive` |
| `status` | VARCHAR(20) | Estado de entrega: `channel_delivered`, `channel_read`, `channel_sent` |
| `contact_name` | VARCHAR(255) | Nombre del contacto |
| `contact_id` | VARCHAR(100) | ID del contacto (FK → contacts) |
| `conversation_id` | VARCHAR(100) | ID de sesion de agente |
| `agent_id` | VARCHAR(100) | ID del agente (FK → agents) |
| `close_reason` | VARCHAR(100) | Razon de cierre: `AGENT_ACTION`, `AGENT_TRANSFER`, etc. |
| `intent` | VARCHAR(200) | Intent de Dialogflow (ej: `Default Fallback Intent`) |
| `is_fallback` | BOOLEAN | True si fue fallback de Dialogflow |
| `message_body` | TEXT | Contenido del mensaje |
| `is_bot` | BOOLEAN | True si fue respuesta del bot (integration=df, sendType!=input) |
| `is_human` | BOOLEAN | True si fue respuesta de agente humano (sendType=operator) |
| `wait_time_seconds` | INTEGER | Tiempo de espera del contacto |
| `handle_time_seconds` | INTEGER | Tiempo de atencion del agente |

**Unique**: `(tenant_id, message_id)`
**Indices**: tenant+date, tenant+direction, tenant+contact_id, tenant+conversation_id

**Reglas de derivacion de `direction`:**
| send_type | integration | → direction |
|---|---|---|
| `input` | cualquiera | `Inbound` |
| `operator` | cualquiera | `Agent` |
| `dialogflow` | cualquiera | `Bot` |
| `agent_notification` | cualquiera | `System` |
| otro | `df` | `Bot` |
| otro | otro | `Outbound` |

---

#### `chat_conversations` — Sesiones de agente

Fuente: `/v1/chat/agent/conversations` via transform_bridge

| Columna | Tipo | Descripcion |
|---|---|---|
| `id` | SERIAL PK | |
| `tenant_id` | TEXT | Tenant (RLS) |
| `session_id` | VARCHAR(100) | `agentSessionId` — ID unico de la sesion |
| `conversation_session_id` | VARCHAR(100) | `conversationSessionId` — ID de la conversacion global |
| `contact_id` | VARCHAR(100) | ID del contacto atendido |
| `agent_id` | VARCHAR(100) | ID del agente que atendio |
| `agent_email` | VARCHAR(255) | Email del agente |
| `channel` | VARCHAR(30) | Canal: `cloudapi` (WhatsApp), `webchat` |
| `queued_at` | TIMESTAMPTZ | Momento en que entro a la cola |
| `assigned_at` | TIMESTAMPTZ | Momento en que fue asignado a un agente |
| `closed_at` | TIMESTAMPTZ | Momento de cierre |
| `initial_session_id` | VARCHAR(100) | Sesion inicial (antes de transferencia) |
| `wait_time_seconds` | INTEGER | Segundos entre queued_at y assigned_at (calculado) |
| `handle_time_seconds` | INTEGER | Segundos entre assigned_at y closed_at (calculado) |

**Unique**: `(tenant_id, session_id)`
**Indices**: tenant+closed_at, tenant+agent_id, tenant+contact_id

---

#### `chat_channels` — Canales de WhatsApp/webchat

Fuente: `/v1/chat/channel` via transform_bridge

| Columna | Tipo | Descripcion |
|---|---|---|
| `id` | SERIAL PK | |
| `tenant_id` | TEXT | Tenant (RLS) |
| `channel_id` | VARCHAR(100) | ID del canal |
| `channel_type` | VARCHAR(30) | Tipo: `cloudapi`, `webchat` |
| `channel_name` | VARCHAR(255) | Nombre descriptivo |
| `phone_number` | VARCHAR(50) | Numero de telefono (WhatsApp) |
| `status` | VARCHAR(20) | Estado del canal |
| `config` | JSONB | Configuracion completa del canal |

**Unique**: `(tenant_id, channel_id)`

---

#### `contacts` — Dimension: contactos

Fuente: `/v1/chat/contacts` via transform_bridge

| Columna | Tipo | Descripcion |
|---|---|---|
| `id` | SERIAL PK | |
| `tenant_id` | TEXT | Tenant (RLS) |
| `contact_id` | VARCHAR(100) | ID del contacto (telefono o hash) |
| `contact_name` | VARCHAR(255) | Nombre de perfil de WhatsApp |
| `total_messages` | INTEGER | Total mensajes (actualizado post-transform) |
| `first_contact` | DATE | Primera interaccion |
| `last_contact` | DATE | Ultima interaccion |
| `total_conversations` | INTEGER | Total conversaciones |

**Unique**: `(tenant_id, contact_id)`

---

#### `agents` — Dimension: agentes

Fuente: Derivado de `chat_conversations` via post-transform

| Columna | Tipo | Descripcion |
|---|---|---|
| `id` | SERIAL PK | |
| `tenant_id` | TEXT | Tenant (RLS) |
| `agent_id` | VARCHAR(100) | ID del agente en Indigitall |
| `total_messages` | INTEGER | Total mensajes atendidos |
| `conversations_handled` | INTEGER | Total sesiones atendidas |
| `avg_handle_time_seconds` | INTEGER | Tiempo promedio de atencion |

**Unique**: `(tenant_id, agent_id)`

---

#### `daily_stats` — Estadisticas diarias agregadas

Fuente: Combinacion de push stats + mensajes chat via transform_bridge

| Columna | Tipo | Descripcion |
|---|---|---|
| `id` | SERIAL PK | |
| `tenant_id` | TEXT | Tenant (RLS) |
| `date` | DATE | Fecha |
| `total_messages` | INTEGER | Total mensajes del dia (push + chat) |
| `unique_contacts` | INTEGER | Contactos unicos del dia |
| `conversations` | INTEGER | Conversaciones del dia |
| `fallback_count` | INTEGER | Fallbacks de Dialogflow |

**Unique**: `(tenant_id, date)`

---

### Dominio: Campanas (Push/SMS/Email)

#### `toques_daily` — Metricas diarias de push notifications

Fuente: `/v1/application/{id}/dateStats` via transform_bridge

| Columna | Tipo | Descripcion |
|---|---|---|
| `tenant_id` | TEXT | Tenant |
| `date` | DATE | Fecha |
| `canal` | VARCHAR(30) | Plataforma: `ios`, `android`, `web` |
| `proyecto_cuenta` | VARCHAR(100) | Application ID |
| `enviados` | INTEGER | Push enviados |
| `entregados` | INTEGER | Push entregados |
| `clicks` | INTEGER | Clicks en push |
| `abiertos` | INTEGER | Push abiertos |
| `ctr` | NUMERIC(6,2) | Click-through rate (%) |
| `tasa_entrega` | NUMERIC(6,2) | Tasa de entrega (%) |
| `open_rate` | NUMERIC(6,2) | Tasa de apertura (%) |

**Unique**: `(tenant_id, date, canal, proyecto_cuenta)`

---

#### `campaigns` — Campanas

Fuente: `/v1/campaign` via transform_bridge

| Columna | Tipo | Descripcion |
|---|---|---|
| `tenant_id` | TEXT | Tenant |
| `campana_id` | VARCHAR(100) | ID de la campana |
| `campana_nombre` | VARCHAR(255) | Nombre |
| `canal` | VARCHAR(30) | Canal (push, sms, email) |
| `tipo_campana` | VARCHAR(50) | Estado/tipo |
| `total_enviados` | INTEGER | Total enviados |
| `total_entregados` | INTEGER | Total entregados |
| `total_clicks` | INTEGER | Total clicks |
| `fecha_inicio` | DATE | Inicio |
| `fecha_fin` | DATE | Fin |
| `ctr` | NUMERIC(6,2) | CTR (%) |

**Unique**: `(tenant_id, campana_id)`

---

#### `toques_heatmap` — Engagement por hora/dia

Fuente: `/v1/application/{id}/pushHeatmap` via transform_bridge

| Columna | Tipo | Descripcion |
|---|---|---|
| `tenant_id` | TEXT | Tenant |
| `canal` | VARCHAR(30) | Canal |
| `dia_semana` | VARCHAR(12) | Dia de la semana (monday, tuesday, etc.) |
| `hora` | SMALLINT | Hora (0-23) |
| `ctr` | NUMERIC(6,2) | CTR para esa combinacion dia+hora |
| `dia_orden` | SMALLINT | Orden numerico (1=lunes, 7=domingo) |

**Unique**: `(tenant_id, canal, dia_semana, hora)`

---

### Dominio: Aplicacion

#### `sync_state` — Estado de sincronizacion ETL

| Columna | Tipo | Descripcion |
|---|---|---|
| `tenant_id` | TEXT | Tenant |
| `entity` | VARCHAR(50) | Entidad: contacts, messages, toques_daily, etc. |
| `last_cursor` | TEXT | Cursor de paginacion para sync incremental |
| `last_sync_at` | TIMESTAMPTZ | Ultima sincronizacion exitosa |
| `records_synced` | INTEGER | Registros sincronizados en ultima ejecucion |
| `status` | VARCHAR(20) | Estado: `success`, `error`, `pending`, `running` |

**Unique**: `(tenant_id, entity)`

---

## Pipeline de Datos

### Extractores (scripts/extractors/)

| Extractor | Tabla raw | Endpoints |
|---|---|---|
| `ChatExtractor` | `raw.raw_chat_stats` | `/v1/chat/contacts`, `/chat/agent/status`, `/chat/history/csv`, `/chat/agent/conversations`, `/chat/channel`, `/chat/configuration`, `/chat/topic`, `/chat/integration` |
| `PushExtractor` | `raw.raw_push_stats` | `/v1/application/{id}/dateStats`, `/pushHeatmap`, `/stats/device` |
| `CampaignsExtractor` | `raw.raw_campaigns_api` | `/v1/campaign` |
| `ContactsExtractor` | `raw.raw_contacts_api` | `/v1/chat/contacts` |

### Transform Bridge (scripts/transform_bridge.py)

Orden de ejecucion (respeta dependencias FK):

```
1. contacts         — raw.raw_contacts_api    → public.contacts
2. daily_stats      — raw.raw_push_stats      → public.daily_stats
3. toques_daily     — raw.raw_push_stats      → public.toques_daily
4. toques_heatmap   — raw.raw_push_stats      → public.toques_heatmap
5. campaigns        — raw.raw_campaigns_api   → public.campaigns
6. messages         — raw.raw_chat_stats      → public.messages        [NUEVO]
7. chat_conversations — raw.raw_chat_stats    → public.chat_conversations [NUEVO]
8. chat_channels    — raw.raw_chat_stats      → public.chat_channels   [NUEVO]

Post-transforms:
  - daily_stats ← aggregar totales de toques_daily
  - daily_stats ← aggregar totales de messages (chat)
  - agents ← aggregar metricas de chat_conversations
```

### Orquestacion n8n

| Workflow | Frecuencia | Accion |
|---|---|---|
| `indigitall-data-sync` | Cada 6 horas | ETL completo: extract + transform + dbt |
| `indigitall-transform-only` | Cada 1 hora | Solo transform + dbt (re-procesa raw existente) |

Ambos disparan `POST /api/run-pipeline` en la app Dash.

---

## Endpoints API de Indigitall

**Base URL**: `https://am1.api.indigitall.com`
**Auth**: `Authorization: ServerKey <UUID>`
**App ID**: `100274` (VISIONAMOS PROD)

| Endpoint | Metodo | Descripcion | Paginacion |
|---|---|---|---|
| `/v1/chat/history/csv` | GET | Historial de mensajes (CSV) | `limit` + `page` + `dateFrom` + `dateTo` (max 7 dias) |
| `/v1/chat/agent/conversations` | GET | Sesiones de agente | `email=""` + `limit=50000` |
| `/v1/chat/contacts` | GET | Lista de contactos | `limit` + `page` |
| `/v1/chat/agent/status` | GET | Agentes activos | Sin paginacion |
| `/v1/chat/channel` | GET | Canales WhatsApp/webchat | Sin paginacion |
| `/v1/chat/configuration` | GET | Config del chat | Sin paginacion |
| `/v1/chat/topic` | GET | Topics de conversacion | Sin paginacion |
| `/v1/chat/integration` | GET | Integraciones (Dialogflow, agentes) | Sin paginacion |
| `/v1/application/{id}/dateStats` | GET | Stats push por dia | `dateFrom` + `dateTo` |
| `/v1/application/{id}/pushHeatmap` | GET | Heatmap push | `dateFrom` + `dateTo` |
| `/v1/campaign` | GET | Lista de campanas | `limit` + `page` |

---

## Infraestructura

```
┌─────────────────────────────────────────────────────┐
│                Docker Compose                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  PostgreSQL (Supabase)  ← raw.* + public.* schemas  │
│  PostgREST              ← API REST automatica        │
│  Supabase Studio        ← Admin UI (:3000)           │
│  Kong API Gateway       ← Auth + routing             │
│  Dash App               ← BI dashboards (:8050)      │
│  n8n                    ← Workflow automation (:5678) │
│                                                     │
└─────────────────────────────────────────────────────┘

Deploy: GitHub Actions → SSH → GCP VM
VM: indigitall-analytics (34.151.199.149)
Reverse Proxy: Caddy (TLS automatico)

URLs:
  - https://analytics.abstractstudio.co (Dash)
  - https://n8n-indigitall.abstractstudio.co (n8n)
  - https://studio-indigitall.abstractstudio.co (Supabase Studio)
```

---

## Datos de Referencia

| Campo | Valor |
|---|---|
| Proyecto GCP | `trax-report-automation` |
| VM | `indigitall-analytics` |
| IP | `34.151.199.149` |
| Zona | `southamerica-east1-a` |
| Tenant | `visionamos` |
| App ID | `100274` |
| API Region | `am1` (Americas) |
