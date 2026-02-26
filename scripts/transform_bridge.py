"""
Phase 2c — Transform Bridge: raw.* JSONB → public.* structured tables.

Reads flattened data from staging SQL (same logic as dbt stg_raw_* models)
and UPSERTs into public.* tables matching app/models/schemas.py definitions.

Usage:
    docker compose exec app python scripts/transform_bridge.py
    python scripts/transform_bridge.py          # local (requires .env)

Rules:
    - tenant_id = 'visionamos' for all records
    - All timestamps stored as TIMESTAMPTZ (UTC)
    - NEVER deletes from raw.* tables
    - Idempotent — safe to re-run
"""

import json as _json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.database import engine

TENANT_ID = "visionamos"
APP_ID = "100274"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def update_sync_state(conn, entity: str, records: int, status: str = "success"):
    """UPSERT sync_state for the given entity."""
    conn.execute(text("""
        INSERT INTO public.sync_state (tenant_id, entity, last_sync_at, records_synced, status)
        VALUES (:tid, :entity, :ts, :records, :status)
        ON CONFLICT (tenant_id, entity) DO UPDATE SET
            last_sync_at   = EXCLUDED.last_sync_at,
            records_synced = EXCLUDED.records_synced,
            status         = EXCLUDED.status
    """), {
        "tid": TENANT_ID,
        "entity": entity,
        "ts": datetime.now(timezone.utc),
        "records": records,
        "status": status,
    })


# ---------------------------------------------------------------------------
# Transform: contacts
# ---------------------------------------------------------------------------

CONTACTS_SQL = """
WITH raw_rows AS (
    SELECT
        source_data,
        coalesce(tenant_id, :tid) AS tenant_id,
        loaded_at
    FROM raw.raw_contacts_api
    WHERE source_data->'data' IS NOT NULL
      AND jsonb_typeof(source_data->'data') = 'array'
),
flattened AS (
    SELECT
        r.tenant_id,
        elem->>'contactId'                       AS contact_id,
        elem->>'profileName'                      AS contact_name,
        (elem->>'createdAt')::timestamptz::date   AS first_contact,
        (elem->>'updatedAt')::timestamptz::date   AS last_contact,
        r.loaded_at
    FROM raw_rows r,
         jsonb_array_elements(r.source_data->'data') AS elem
    WHERE elem->>'contactId' IS NOT NULL
),
deduplicated AS (
    SELECT *,
        row_number() OVER (
            PARTITION BY tenant_id, contact_id
            ORDER BY last_contact DESC NULLS LAST, loaded_at DESC
        ) AS _rn
    FROM flattened
)
SELECT tenant_id, contact_id, contact_name, first_contact, last_contact
FROM deduplicated WHERE _rn = 1
"""

CONTACTS_UPSERT = """
INSERT INTO public.contacts
    (tenant_id, contact_id, contact_name, total_messages, first_contact, last_contact, total_conversations)
VALUES
    (:tenant_id, :contact_id, :contact_name, 0, :first_contact, :last_contact, 0)
ON CONFLICT (tenant_id, contact_id) DO UPDATE SET
    contact_name  = EXCLUDED.contact_name,
    first_contact = LEAST(contacts.first_contact, EXCLUDED.first_contact),
    last_contact  = GREATEST(contacts.last_contact, EXCLUDED.last_contact)
"""


def transform_contacts(conn) -> int:
    rows = conn.execute(text(CONTACTS_SQL), {"tid": TENANT_ID}).fetchall()
    count = 0
    for r in rows:
        conn.execute(text(CONTACTS_UPSERT), {
            "tenant_id": r[0],
            "contact_id": r[1],
            "contact_name": r[2],
            "first_contact": r[3],
            "last_contact": r[4],
        })
        count += 1
    return count


# ---------------------------------------------------------------------------
# Transform: toques_daily
# ---------------------------------------------------------------------------

TOQUES_DAILY_SQL = """
WITH raw_rows AS (
    SELECT
        source_data,
        coalesce(tenant_id, :tid) AS tenant_id,
        coalesce(application_id, :app_id) AS application_id,
        loaded_at
    FROM raw.raw_push_stats
    WHERE endpoint LIKE '%%/dateStats%%'
      AND source_data->'data' IS NOT NULL
      AND jsonb_typeof(source_data->'data') = 'array'
),
flattened AS (
    SELECT
        r.tenant_id,
        r.application_id                               AS proyecto_cuenta,
        elem->>'platformGroup'                          AS canal,
        (elem->>'statsDate')::date                      AS date,
        coalesce((elem->>'numDevicesSent')::int, 0)     AS enviados,
        coalesce((elem->>'numDevicesSuccess')::int, 0)  AS entregados,
        coalesce((elem->>'numDevicesReceived')::int, 0) AS abiertos,
        coalesce((elem->>'numDevicesClicked')::int, 0)  AS clicks,
        r.loaded_at
    FROM raw_rows r,
         jsonb_array_elements(r.source_data->'data') AS elem
    WHERE elem->>'platformGroup' IS NOT NULL
      AND elem->>'statsDate' IS NOT NULL
),
deduplicated AS (
    SELECT *,
        row_number() OVER (
            PARTITION BY tenant_id, date, canal, proyecto_cuenta
            ORDER BY loaded_at DESC
        ) AS _rn
    FROM flattened
)
SELECT tenant_id, date, canal, proyecto_cuenta, enviados, entregados, abiertos, clicks
FROM deduplicated WHERE _rn = 1
"""

TOQUES_DAILY_UPSERT = """
INSERT INTO public.toques_daily
    (tenant_id, date, canal, proyecto_cuenta,
     enviados, entregados, clicks, chunks, usuarios_unicos,
     abiertos, rebotes, bloqueados, spam, desuscritos, conversiones,
     ctr, tasa_entrega, open_rate, conversion_rate)
VALUES
    (:tenant_id, :date, :canal, :proyecto_cuenta,
     :enviados, :entregados, :clicks, 0, 0,
     :abiertos, 0, 0, 0, 0, 0,
     :ctr, :tasa_entrega, :open_rate, 0)
ON CONFLICT (tenant_id, date, canal, proyecto_cuenta) DO UPDATE SET
    enviados     = EXCLUDED.enviados,
    entregados   = EXCLUDED.entregados,
    clicks       = EXCLUDED.clicks,
    abiertos     = EXCLUDED.abiertos,
    ctr          = EXCLUDED.ctr,
    tasa_entrega = EXCLUDED.tasa_entrega,
    open_rate    = EXCLUDED.open_rate
"""


def transform_toques_daily(conn) -> int:
    rows = conn.execute(text(TOQUES_DAILY_SQL), {"tid": TENANT_ID, "app_id": APP_ID}).fetchall()
    count = 0
    for r in rows:
        enviados = r[4]
        entregados = r[5]
        abiertos = r[6]
        clicks = r[7]
        ctr = round(clicks / enviados * 100, 2) if enviados > 0 else 0
        tasa_entrega = round(entregados / enviados * 100, 2) if enviados > 0 else 0
        open_rate = round(abiertos / entregados * 100, 2) if entregados > 0 else 0

        conn.execute(text(TOQUES_DAILY_UPSERT), {
            "tenant_id": r[0],
            "date": r[1],
            "canal": r[2],
            "proyecto_cuenta": r[3],
            "enviados": enviados,
            "entregados": entregados,
            "clicks": clicks,
            "abiertos": abiertos,
            "ctr": ctr,
            "tasa_entrega": tasa_entrega,
            "open_rate": open_rate,
        })
        count += 1
    return count


# ---------------------------------------------------------------------------
# Transform: toques_heatmap
# ---------------------------------------------------------------------------

HEATMAP_SQL = """
WITH raw_rows AS (
    SELECT
        source_data,
        coalesce(tenant_id, :tid) AS tenant_id,
        loaded_at
    FROM raw.raw_push_stats
    WHERE endpoint LIKE '%%/pushHeatmap%%'
      AND source_data->'data' IS NOT NULL
      AND jsonb_typeof(source_data->'data') = 'object'
),
latest AS (
    SELECT *,
        row_number() OVER (PARTITION BY tenant_id ORDER BY loaded_at DESC) AS _rn
    FROM raw_rows
),
weekday_entries AS (
    SELECT
        l.tenant_id,
        weekday_key,
        weekday_val
    FROM latest l,
         jsonb_each(l.source_data->'data'->'weekday-hour') AS wd(weekday_key, weekday_val)
    WHERE l._rn = 1
      AND jsonb_typeof(weekday_val) = 'object'
),
flattened AS (
    SELECT
        w.tenant_id,
        'push' AS canal,
        w.weekday_key AS dia_semana,
        hour_key::smallint AS hora,
        round((hour_val::text)::numeric * 100, 2) AS ctr,
        CASE w.weekday_key
            WHEN 'monday'    THEN 1
            WHEN 'tuesday'   THEN 2
            WHEN 'wednesday' THEN 3
            WHEN 'thursday'  THEN 4
            WHEN 'friday'    THEN 5
            WHEN 'saturday'  THEN 6
            WHEN 'sunday'    THEN 7
            ELSE 0
        END AS dia_orden
    FROM weekday_entries w,
         jsonb_each(w.weekday_val) AS h(hour_key, hour_val)
)
SELECT tenant_id, canal, dia_semana, hora, ctr, dia_orden
FROM flattened
"""

HEATMAP_UPSERT = """
INSERT INTO public.toques_heatmap
    (tenant_id, canal, dia_semana, hora, enviados, clicks, abiertos, conversiones, ctr, dia_orden)
VALUES
    (:tenant_id, :canal, :dia_semana, :hora, 0, 0, 0, 0, :ctr, :dia_orden)
ON CONFLICT (tenant_id, canal, dia_semana, hora) DO UPDATE SET
    ctr       = EXCLUDED.ctr,
    dia_orden = EXCLUDED.dia_orden
"""


def transform_heatmap(conn) -> int:
    rows = conn.execute(text(HEATMAP_SQL), {"tid": TENANT_ID}).fetchall()
    count = 0
    for r in rows:
        conn.execute(text(HEATMAP_UPSERT), {
            "tenant_id": r[0],
            "canal": r[1],
            "dia_semana": r[2],
            "hora": int(r[3]),
            "ctr": float(r[4]),
            "dia_orden": int(r[5]),
        })
        count += 1
    return count


# ---------------------------------------------------------------------------
# Transform: campaigns
# ---------------------------------------------------------------------------

CAMPAIGNS_SQL = """
WITH raw_rows AS (
    SELECT
        source_data,
        coalesce(tenant_id, :tid) AS tenant_id,
        loaded_at
    FROM raw.raw_campaigns_api
    WHERE source_data->'data' IS NOT NULL
      AND jsonb_typeof(source_data->'data') = 'array'
),
flattened AS (
    SELECT
        r.tenant_id,
        coalesce(elem->>'id', elem->>'campaignId')             AS campana_id,
        coalesce(elem->>'name', elem->>'title', 'Sin nombre')  AS campana_nombre,
        coalesce(elem->>'channel', elem->>'type', 'push')      AS canal,
        coalesce(elem->>'applicationId', :app_id)               AS proyecto_cuenta,
        elem->>'status'                                         AS tipo_campana,
        coalesce((elem->>'sent')::int, 0)                       AS total_enviados,
        coalesce((elem->>'delivered')::int, 0)                  AS total_entregados,
        coalesce((elem->>'clicked')::int, 0)                    AS total_clicks,
        (elem->>'startDate')::date                              AS fecha_inicio,
        (elem->>'endDate')::date                                AS fecha_fin,
        coalesce((elem->>'opened')::int, 0)                     AS total_abiertos,
        coalesce((elem->>'bounced')::int, 0)                    AS total_rebotes,
        coalesce((elem->>'blocked')::int, 0)                    AS total_bloqueados,
        coalesce((elem->>'spam')::int, 0)                       AS total_spam,
        coalesce((elem->>'unsubscribed')::int, 0)               AS total_desuscritos,
        coalesce((elem->>'converted')::int, 0)                  AS total_conversiones,
        r.loaded_at
    FROM raw_rows r,
         jsonb_array_elements(r.source_data->'data') AS elem
),
deduplicated AS (
    SELECT *,
        row_number() OVER (
            PARTITION BY tenant_id, campana_id
            ORDER BY loaded_at DESC
        ) AS _rn
    FROM flattened
    WHERE campana_id IS NOT NULL
)
SELECT tenant_id, campana_id, campana_nombre, canal, proyecto_cuenta, tipo_campana,
       total_enviados, total_entregados, total_clicks, fecha_inicio, fecha_fin,
       total_abiertos, total_rebotes, total_bloqueados, total_spam,
       total_desuscritos, total_conversiones
FROM deduplicated WHERE _rn = 1
"""

CAMPAIGNS_UPSERT = """
INSERT INTO public.campaigns
    (tenant_id, campana_id, campana_nombre, canal, proyecto_cuenta, tipo_campana,
     total_enviados, total_entregados, total_clicks, total_chunks,
     fecha_inicio, fecha_fin,
     total_abiertos, total_rebotes, total_bloqueados, total_spam,
     total_desuscritos, total_conversiones,
     ctr, tasa_entrega, open_rate, conversion_rate)
VALUES
    (:tenant_id, :campana_id, :campana_nombre, :canal, :proyecto_cuenta, :tipo_campana,
     :total_enviados, :total_entregados, :total_clicks, 0,
     :fecha_inicio, :fecha_fin,
     :total_abiertos, :total_rebotes, :total_bloqueados, :total_spam,
     :total_desuscritos, :total_conversiones,
     :ctr, :tasa_entrega, :open_rate, :conversion_rate)
ON CONFLICT (tenant_id, campana_id) DO UPDATE SET
    campana_nombre    = EXCLUDED.campana_nombre,
    canal             = EXCLUDED.canal,
    proyecto_cuenta   = EXCLUDED.proyecto_cuenta,
    tipo_campana      = EXCLUDED.tipo_campana,
    total_enviados    = EXCLUDED.total_enviados,
    total_entregados  = EXCLUDED.total_entregados,
    total_clicks      = EXCLUDED.total_clicks,
    fecha_inicio      = EXCLUDED.fecha_inicio,
    fecha_fin         = EXCLUDED.fecha_fin,
    total_abiertos    = EXCLUDED.total_abiertos,
    total_rebotes     = EXCLUDED.total_rebotes,
    total_bloqueados  = EXCLUDED.total_bloqueados,
    total_spam        = EXCLUDED.total_spam,
    total_desuscritos = EXCLUDED.total_desuscritos,
    total_conversiones = EXCLUDED.total_conversiones,
    ctr               = EXCLUDED.ctr,
    tasa_entrega      = EXCLUDED.tasa_entrega,
    open_rate         = EXCLUDED.open_rate,
    conversion_rate   = EXCLUDED.conversion_rate
"""


def transform_campaigns(conn) -> int:
    rows = conn.execute(text(CAMPAIGNS_SQL), {"tid": TENANT_ID, "app_id": APP_ID}).fetchall()
    count = 0
    for r in rows:
        enviados = r[6]
        entregados = r[7]
        clicks = r[8]
        abiertos = r[11]
        conversiones = r[16]

        ctr = round(clicks / enviados * 100, 2) if enviados > 0 else 0
        tasa_entrega = round(entregados / enviados * 100, 2) if enviados > 0 else 0
        open_rate = round(abiertos / entregados * 100, 2) if entregados > 0 else 0
        conversion_rate = round(conversiones / clicks * 100, 2) if clicks > 0 else 0

        conn.execute(text(CAMPAIGNS_UPSERT), {
            "tenant_id": r[0],
            "campana_id": r[1],
            "campana_nombre": r[2],
            "canal": r[3],
            "proyecto_cuenta": r[4],
            "tipo_campana": r[5],
            "total_enviados": enviados,
            "total_entregados": entregados,
            "total_clicks": clicks,
            "fecha_inicio": r[9],
            "fecha_fin": r[10],
            "total_abiertos": abiertos,
            "total_rebotes": r[12],
            "total_bloqueados": r[13],
            "total_spam": r[14],
            "total_desuscritos": r[15],
            "total_conversiones": conversiones,
            "ctr": ctr,
            "tasa_entrega": tasa_entrega,
            "open_rate": open_rate,
            "conversion_rate": conversion_rate,
        })
        count += 1
    return count


# ---------------------------------------------------------------------------
# Transform: daily_stats (aggregated from toques_daily)
# ---------------------------------------------------------------------------

DAILY_STATS_SQL = """
WITH raw_dates AS (
    SELECT
        coalesce(tenant_id, :tid) AS tenant_id,
        elem->>'statsDate' AS stats_date
    FROM raw.raw_push_stats,
         jsonb_array_elements(source_data->'data') AS elem
    WHERE endpoint LIKE '%%/dateStats%%'
      AND source_data->'data' IS NOT NULL
      AND jsonb_typeof(source_data->'data') = 'array'
      AND elem->>'statsDate' IS NOT NULL
)
SELECT
    tenant_id,
    stats_date::date AS date,
    0 AS total_messages,
    0 AS unique_contacts,
    0 AS conversations,
    0 AS fallback_count
FROM raw_dates
GROUP BY tenant_id, stats_date::date
"""

DAILY_STATS_UPSERT = """
INSERT INTO public.daily_stats
    (tenant_id, date, total_messages, unique_contacts, conversations, fallback_count)
VALUES
    (:tenant_id, :date, :total_messages, :unique_contacts, :conversations, :fallback_count)
ON CONFLICT (tenant_id, date) DO UPDATE SET
    total_messages  = EXCLUDED.total_messages,
    unique_contacts = EXCLUDED.unique_contacts,
    conversations   = EXCLUDED.conversations,
    fallback_count  = EXCLUDED.fallback_count
"""


def transform_daily_stats(conn) -> int:
    rows = conn.execute(text(DAILY_STATS_SQL), {"tid": TENANT_ID}).fetchall()
    count = 0
    for r in rows:
        conn.execute(text(DAILY_STATS_UPSERT), {
            "tenant_id": r[0],
            "date": r[1],
            "total_messages": r[2],
            "unique_contacts": r[3],
            "conversations": r[4],
            "fallback_count": r[5],
        })
        count += 1
    return count


# ---------------------------------------------------------------------------
# Post-transform: update daily_stats totals from toques_daily
# ---------------------------------------------------------------------------

DAILY_STATS_UPDATE_TOTALS = """
UPDATE public.daily_stats ds SET
    total_messages = sub.total_enviados
FROM (
    SELECT tenant_id, date, coalesce(sum(enviados), 0) AS total_enviados
    FROM public.toques_daily
    WHERE tenant_id = :tid
    GROUP BY tenant_id, date
) sub
WHERE ds.tenant_id = sub.tenant_id AND ds.date = sub.date
"""


def update_daily_stats_totals(conn) -> int:
    result = conn.execute(text(DAILY_STATS_UPDATE_TOTALS), {"tid": TENANT_ID})
    return result.rowcount


# ---------------------------------------------------------------------------
# Transform: messages (from chat/history/csv stored in raw.raw_chat_stats)
# ---------------------------------------------------------------------------

MESSAGES_SQL = """
WITH raw_rows AS (
    SELECT
        source_data,
        coalesce(tenant_id, :tid) AS tenant_id,
        loaded_at
    FROM raw.raw_chat_stats
    WHERE endpoint = '/v1/chat/history/csv'
      AND source_data->'data' IS NOT NULL
      AND jsonb_typeof(source_data->'data') = 'array'
),
flattened AS (
    SELECT
        r.tenant_id,
        elem->>'messageId'                              AS message_id,
        (elem->>'messageDate')::timestamptz             AS msg_timestamp,
        (elem->>'messageDate')::timestamptz::date       AS msg_date,
        EXTRACT(HOUR FROM (elem->>'messageDate')::timestamptz)::smallint AS msg_hour,
        TRIM(TO_CHAR((elem->>'messageDate')::timestamptz, 'Day')) AS day_of_week,
        elem->>'sendType'                               AS send_type,
        elem->>'contentType'                            AS content_type,
        elem->>'status'                                 AS status,
        elem->>'profileName'                            AS contact_name,
        elem->>'contactId'                              AS contact_id,
        elem->>'agentConversationId'                    AS conversation_id,
        elem->>'agentId'                                AS agent_id,
        elem->>'agentCloseReason'                       AS close_reason,
        elem->>'dfIntentName'                           AS intent,
        CASE WHEN elem->>'isFallback' = 'Yes' THEN TRUE ELSE FALSE END AS is_fallback,
        elem->>'content'                                AS message_body,
        elem->>'integration'                            AS integration,
        elem->>'channel'                                AS channel,
        r.loaded_at
    FROM raw_rows r,
         jsonb_array_elements(r.source_data->'data') AS elem
    WHERE elem->>'messageId' IS NOT NULL
),
deduplicated AS (
    SELECT *,
        row_number() OVER (
            PARTITION BY tenant_id, message_id
            ORDER BY loaded_at DESC
        ) AS _rn
    FROM flattened
)
SELECT tenant_id, message_id, msg_timestamp, msg_date, msg_hour, day_of_week,
       send_type, content_type, status, contact_name, contact_id,
       conversation_id, agent_id, close_reason, intent, is_fallback,
       message_body, integration, channel
FROM deduplicated WHERE _rn = 1
"""

MESSAGES_UPSERT = """
INSERT INTO public.messages
    (tenant_id, message_id, timestamp, date, hour, day_of_week,
     send_type, direction, content_type, status, contact_name, contact_id,
     conversation_id, agent_id, close_reason, intent, is_fallback,
     message_body, is_bot, is_human, wait_time_seconds, handle_time_seconds)
VALUES
    (:tenant_id, :message_id, :timestamp, :date, :hour, :day_of_week,
     :send_type, :direction, :content_type, :status, :contact_name, :contact_id,
     :conversation_id, :agent_id, :close_reason, :intent, :is_fallback,
     :message_body, :is_bot, :is_human, NULL, NULL)
ON CONFLICT (tenant_id, message_id) DO UPDATE SET
    send_type     = EXCLUDED.send_type,
    direction     = EXCLUDED.direction,
    content_type  = EXCLUDED.content_type,
    status        = EXCLUDED.status,
    contact_name  = EXCLUDED.contact_name,
    contact_id    = EXCLUDED.contact_id,
    conversation_id = EXCLUDED.conversation_id,
    agent_id      = EXCLUDED.agent_id,
    close_reason  = EXCLUDED.close_reason,
    intent        = EXCLUDED.intent,
    is_fallback   = EXCLUDED.is_fallback,
    message_body  = EXCLUDED.message_body,
    is_bot        = EXCLUDED.is_bot,
    is_human      = EXCLUDED.is_human
"""


def _derive_direction(send_type: str, integration: str, channel: str) -> str:
    """Derive message direction from sendType + integration fields."""
    if send_type == "input":
        return "Inbound"
    elif send_type == "operator":
        return "Agent"
    elif send_type == "dialogflow":
        return "Bot"
    elif send_type == "agent_notification":
        return "System"
    elif integration == "df":
        return "Bot"
    return "Outbound"


def transform_messages(conn) -> int:
    rows = conn.execute(text(MESSAGES_SQL), {"tid": TENANT_ID}).fetchall()
    count = 0
    for r in rows:
        send_type = r[6] or ""
        integration = r[17] or ""
        channel = r[18] or ""
        direction = _derive_direction(send_type, integration, channel)
        is_bot = integration == "df" and send_type != "input"
        is_human = send_type == "operator"

        conn.execute(text(MESSAGES_UPSERT), {
            "tenant_id": r[0],
            "message_id": str(r[1]),
            "timestamp": r[2],
            "date": r[3],
            "hour": int(r[4]) if r[4] is not None else 0,
            "day_of_week": (r[5] or "Unknown")[:10],
            "send_type": send_type[:30] if send_type else None,
            "direction": direction,
            "content_type": (r[7] or "")[:30] if r[7] else None,
            "status": (r[8] or "")[:20] if r[8] else None,
            "contact_name": r[9],
            "contact_id": r[10],
            "conversation_id": str(r[11]) if r[11] else None,
            "agent_id": str(r[12]) if r[12] else None,
            "close_reason": r[13],
            "intent": r[14],
            "is_fallback": r[15],
            "message_body": r[16],
            "is_bot": is_bot,
            "is_human": is_human,
        })
        count += 1
    return count


# ---------------------------------------------------------------------------
# Transform: chat_conversations (from agent/conversations in raw.raw_chat_stats)
# ---------------------------------------------------------------------------

CONVERSATIONS_SQL = """
WITH raw_rows AS (
    SELECT
        source_data,
        coalesce(tenant_id, :tid) AS tenant_id,
        loaded_at
    FROM raw.raw_chat_stats
    WHERE endpoint = '/v1/chat/agent/conversations'
      AND source_data->'data' IS NOT NULL
      AND jsonb_typeof(source_data->'data') = 'array'
),
flattened AS (
    SELECT
        r.tenant_id,
        (elem->>'agentSessionId')::text                 AS session_id,
        (elem->>'conversationSessionId')::text          AS conversation_session_id,
        elem->>'contactId'                              AS contact_id,
        (elem->>'agentId')::text                        AS agent_id,
        elem->>'email'                                  AS agent_email,
        elem->>'channel'                                AS channel,
        (elem->>'queuedAt')::timestamptz                AS queued_at,
        (elem->>'assignedAt')::timestamptz              AS assigned_at,
        (elem->>'closedAt')::timestamptz                AS closed_at,
        (elem->>'initialAgentSession')::text            AS initial_session_id,
        r.loaded_at
    FROM raw_rows r,
         jsonb_array_elements(r.source_data->'data') AS elem
    WHERE elem->>'agentSessionId' IS NOT NULL
),
deduplicated AS (
    SELECT *,
        row_number() OVER (
            PARTITION BY tenant_id, session_id
            ORDER BY loaded_at DESC
        ) AS _rn
    FROM flattened
)
SELECT tenant_id, session_id, conversation_session_id, contact_id, agent_id,
       agent_email, channel, queued_at, assigned_at, closed_at, initial_session_id
FROM deduplicated WHERE _rn = 1
"""

CONVERSATIONS_UPSERT = """
INSERT INTO public.chat_conversations
    (tenant_id, session_id, conversation_session_id, contact_id, agent_id,
     agent_email, channel, queued_at, assigned_at, closed_at,
     initial_session_id, wait_time_seconds, handle_time_seconds)
VALUES
    (:tenant_id, :session_id, :conversation_session_id, :contact_id, :agent_id,
     :agent_email, :channel, :queued_at, :assigned_at, :closed_at,
     :initial_session_id, :wait_time_seconds, :handle_time_seconds)
ON CONFLICT (tenant_id, session_id) DO UPDATE SET
    conversation_session_id = EXCLUDED.conversation_session_id,
    contact_id       = EXCLUDED.contact_id,
    agent_id         = EXCLUDED.agent_id,
    agent_email      = EXCLUDED.agent_email,
    channel          = EXCLUDED.channel,
    queued_at        = EXCLUDED.queued_at,
    assigned_at      = EXCLUDED.assigned_at,
    closed_at        = EXCLUDED.closed_at,
    initial_session_id = EXCLUDED.initial_session_id,
    wait_time_seconds  = EXCLUDED.wait_time_seconds,
    handle_time_seconds = EXCLUDED.handle_time_seconds
"""


def transform_conversations(conn) -> int:
    rows = conn.execute(text(CONVERSATIONS_SQL), {"tid": TENANT_ID}).fetchall()
    count = 0
    for r in rows:
        queued_at = r[7]
        assigned_at = r[8]
        closed_at = r[9]

        wait_secs = None
        if queued_at and assigned_at:
            wait_secs = int((assigned_at - queued_at).total_seconds())

        handle_secs = None
        if assigned_at and closed_at:
            handle_secs = int((closed_at - assigned_at).total_seconds())

        conn.execute(text(CONVERSATIONS_UPSERT), {
            "tenant_id": r[0],
            "session_id": str(r[1]),
            "conversation_session_id": str(r[2]) if r[2] else None,
            "contact_id": r[3],
            "agent_id": str(r[4]) if r[4] else None,
            "agent_email": r[5],
            "channel": r[6],
            "queued_at": queued_at,
            "assigned_at": assigned_at,
            "closed_at": closed_at,
            "initial_session_id": str(r[10]) if r[10] else None,
            "wait_time_seconds": wait_secs,
            "handle_time_seconds": handle_secs,
        })
        count += 1
    return count


# ---------------------------------------------------------------------------
# Transform: chat_channels (from chat/channel in raw.raw_chat_stats)
# ---------------------------------------------------------------------------

CHANNELS_SQL = """
WITH raw_rows AS (
    SELECT
        source_data,
        coalesce(tenant_id, :tid) AS tenant_id,
        loaded_at
    FROM raw.raw_chat_stats
    WHERE endpoint = '/v1/chat/channel'
      AND source_data->'data' IS NOT NULL
      AND jsonb_typeof(source_data->'data') = 'array'
),
flattened AS (
    SELECT
        r.tenant_id,
        coalesce(elem->>'id', elem->>'channelId')::text AS channel_id,
        elem->>'type'                                   AS channel_type,
        elem->>'name'                                   AS channel_name,
        elem->>'phoneNumber'                            AS phone_number,
        elem->>'status'                                 AS status,
        elem                                            AS config,
        r.loaded_at
    FROM raw_rows r,
         jsonb_array_elements(r.source_data->'data') AS elem
),
deduplicated AS (
    SELECT *,
        row_number() OVER (
            PARTITION BY tenant_id, channel_id
            ORDER BY loaded_at DESC
        ) AS _rn
    FROM flattened
    WHERE channel_id IS NOT NULL
)
SELECT tenant_id, channel_id, channel_type, channel_name, phone_number, status, config
FROM deduplicated WHERE _rn = 1
"""

CHANNELS_UPSERT = """
INSERT INTO public.chat_channels
    (tenant_id, channel_id, channel_type, channel_name, phone_number, status, config)
VALUES
    (:tenant_id, :channel_id, :channel_type, :channel_name, :phone_number, :status, :config)
ON CONFLICT (tenant_id, channel_id) DO UPDATE SET
    channel_type = EXCLUDED.channel_type,
    channel_name = EXCLUDED.channel_name,
    phone_number = EXCLUDED.phone_number,
    status       = EXCLUDED.status,
    config       = EXCLUDED.config
"""


def transform_channels(conn) -> int:
    rows = conn.execute(text(CHANNELS_SQL), {"tid": TENANT_ID}).fetchall()
    count = 0
    for r in rows:
        config_val = r[6]
        if config_val and not isinstance(config_val, str):
            config_val = _json.dumps(config_val) if not isinstance(config_val, dict) else config_val

        conn.execute(text(CHANNELS_UPSERT), {
            "tenant_id": r[0],
            "channel_id": str(r[1]),
            "channel_type": r[2],
            "channel_name": r[3],
            "phone_number": r[4],
            "status": r[5],
            "config": config_val,
        })
        count += 1
    return count


# ---------------------------------------------------------------------------
# Transform: chat_topics (from chat/topic in raw.raw_chat_stats)
# ---------------------------------------------------------------------------

TOPICS_SQL = """
WITH raw_rows AS (
    SELECT
        source_data,
        coalesce(tenant_id, :tid) AS tenant_id,
        loaded_at
    FROM raw.raw_chat_stats
    WHERE endpoint = '/v1/chat/topic'
      AND source_data->'data' IS NOT NULL
      AND jsonb_typeof(source_data->'data') = 'array'
),
flattened AS (
    SELECT
        r.tenant_id,
        coalesce(elem->>'id', elem->>'topicId')::text   AS topic_id,
        elem->>'name'                                     AS topic_name,
        elem->>'description'                              AS description,
        coalesce((elem->>'isActive')::boolean, true)      AS is_active,
        r.loaded_at
    FROM raw_rows r,
         jsonb_array_elements(r.source_data->'data') AS elem
),
deduplicated AS (
    SELECT *,
        row_number() OVER (
            PARTITION BY tenant_id, topic_id
            ORDER BY loaded_at DESC
        ) AS _rn
    FROM flattened
    WHERE topic_id IS NOT NULL
)
SELECT tenant_id, topic_id, topic_name, description, is_active
FROM deduplicated WHERE _rn = 1
"""

TOPICS_UPSERT = """
INSERT INTO public.chat_topics
    (tenant_id, topic_id, topic_name, description, is_active)
VALUES
    (:tenant_id, :topic_id, :topic_name, :description, :is_active)
ON CONFLICT (tenant_id, topic_id) DO UPDATE SET
    topic_name  = EXCLUDED.topic_name,
    description = EXCLUDED.description,
    is_active   = EXCLUDED.is_active
"""


def transform_topics(conn) -> int:
    rows = conn.execute(text(TOPICS_SQL), {"tid": TENANT_ID}).fetchall()
    count = 0
    for r in rows:
        conn.execute(text(TOPICS_UPSERT), {
            "tenant_id": r[0],
            "topic_id": str(r[1]),
            "topic_name": r[2],
            "description": r[3],
            "is_active": r[4],
        })
        count += 1
    return count


# ---------------------------------------------------------------------------
# Post-transform: update daily_stats from messages + conversations
# ---------------------------------------------------------------------------

DAILY_STATS_FROM_MESSAGES = """
WITH msg_stats AS (
    SELECT
        tenant_id,
        date,
        count(*) AS total_messages,
        count(DISTINCT contact_id) AS unique_contacts,
        count(DISTINCT conversation_id) FILTER (WHERE conversation_id IS NOT NULL) AS conversations,
        count(*) FILTER (WHERE is_fallback = TRUE) AS fallback_count
    FROM public.messages
    WHERE tenant_id = :tid
    GROUP BY tenant_id, date
)
INSERT INTO public.daily_stats
    (tenant_id, date, total_messages, unique_contacts, conversations, fallback_count)
SELECT tenant_id, date, total_messages, unique_contacts, conversations, fallback_count
FROM msg_stats
ON CONFLICT (tenant_id, date) DO UPDATE SET
    total_messages  = GREATEST(daily_stats.total_messages, EXCLUDED.total_messages),
    unique_contacts = GREATEST(daily_stats.unique_contacts, EXCLUDED.unique_contacts),
    conversations   = GREATEST(daily_stats.conversations, EXCLUDED.conversations),
    fallback_count  = GREATEST(daily_stats.fallback_count, EXCLUDED.fallback_count)
"""


def update_daily_stats_from_messages(conn) -> int:
    result = conn.execute(text(DAILY_STATS_FROM_MESSAGES), {"tid": TENANT_ID})
    return result.rowcount


# ---------------------------------------------------------------------------
# Post-transform: update agents from conversations
# ---------------------------------------------------------------------------

AGENTS_FROM_CONVERSATIONS = """
WITH agent_stats AS (
    SELECT
        tenant_id,
        agent_id,
        count(*) AS conversations_handled,
        avg(handle_time_seconds) FILTER (WHERE handle_time_seconds IS NOT NULL) AS avg_handle
    FROM public.chat_conversations
    WHERE tenant_id = :tid AND agent_id IS NOT NULL
    GROUP BY tenant_id, agent_id
)
INSERT INTO public.agents
    (tenant_id, agent_id, total_messages, conversations_handled, avg_handle_time_seconds)
SELECT tenant_id, agent_id, 0, conversations_handled, avg_handle::int
FROM agent_stats
ON CONFLICT (tenant_id, agent_id) DO UPDATE SET
    conversations_handled    = EXCLUDED.conversations_handled,
    avg_handle_time_seconds  = EXCLUDED.avg_handle_time_seconds
"""


def update_agents_from_conversations(conn) -> int:
    result = conn.execute(text(AGENTS_FROM_CONVERSATIONS), {"tid": TENANT_ID})
    return result.rowcount


# ---------------------------------------------------------------------------
# Post-transform: update contacts.total_messages and total_conversations
# ---------------------------------------------------------------------------

CONTACTS_FROM_MESSAGES = """
WITH contact_stats AS (
    SELECT
        tenant_id,
        contact_id,
        count(*) AS total_messages,
        count(DISTINCT conversation_id) FILTER (WHERE conversation_id IS NOT NULL) AS total_conversations
    FROM public.messages
    WHERE tenant_id = :tid AND contact_id IS NOT NULL
    GROUP BY tenant_id, contact_id
)
UPDATE public.contacts c SET
    total_messages      = cs.total_messages,
    total_conversations = cs.total_conversations
FROM contact_stats cs
WHERE c.tenant_id = cs.tenant_id AND c.contact_id = cs.contact_id
"""


def update_contacts_from_messages(conn) -> int:
    result = conn.execute(text(CONTACTS_FROM_MESSAGES), {"tid": TENANT_ID})
    return result.rowcount


# ---------------------------------------------------------------------------
# Post-transform: update agents.total_messages from messages
# ---------------------------------------------------------------------------

AGENTS_MESSAGES = """
WITH agent_msg_stats AS (
    SELECT
        tenant_id,
        agent_id,
        count(*) AS total_messages
    FROM public.messages
    WHERE tenant_id = :tid AND agent_id IS NOT NULL
    GROUP BY tenant_id, agent_id
)
UPDATE public.agents a SET
    total_messages = ams.total_messages
FROM agent_msg_stats ams
WHERE a.tenant_id = ams.tenant_id AND a.agent_id = ams.agent_id
"""


def update_agents_messages(conn) -> int:
    result = conn.execute(text(AGENTS_MESSAGES), {"tid": TENANT_ID})
    return result.rowcount


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

TRANSFORMS = [
    ("contacts",            transform_contacts),
    ("daily_stats",         transform_daily_stats),    # must run BEFORE toques_daily (FK dependency)
    ("toques_daily",        transform_toques_daily),
    ("toques_heatmap",      transform_heatmap),
    ("campaigns",           transform_campaigns),
    ("messages",            transform_messages),
    ("chat_conversations",  transform_conversations),
    ("chat_channels",       transform_channels),
    ("chat_topics",         transform_topics),
]


def main():
    print("=" * 60)
    print("  Transform Bridge — raw.* JSONB → public.* tables")
    print("=" * 60)

    start = time.time()
    results = {}

    for entity, transform_fn in TRANSFORMS:
        print(f"\n  [{entity}] Transforming...")
        try:
            with engine.begin() as conn:
                count = transform_fn(conn)
                update_sync_state(conn, entity, count, "success")
            results[entity] = count
            print(f"    {count} rows upserted")
        except Exception as exc:
            results[entity] = -1
            print(f"    [ERROR] {exc}")
            try:
                with engine.begin() as conn:
                    update_sync_state(conn, entity, 0, f"error: {str(exc)[:200]}")
            except Exception:
                pass

    # Post-transform: update daily_stats with aggregated totals from toques_daily
    print(f"\n  [daily_stats] Updating totals from toques_daily...")
    try:
        with engine.begin() as conn:
            updated = update_daily_stats_totals(conn)
        print(f"    {updated} rows updated")
    except Exception as exc:
        print(f"    [ERROR] {exc}")

    # Post-transform: update daily_stats from messages (chat)
    print(f"\n  [daily_stats] Updating from chat messages...")
    try:
        with engine.begin() as conn:
            updated = update_daily_stats_from_messages(conn)
        print(f"    {updated} rows upserted")
    except Exception as exc:
        print(f"    [ERROR] {exc}")

    # Post-transform: update agents from conversations
    print(f"\n  [agents] Updating from chat conversations...")
    try:
        with engine.begin() as conn:
            updated = update_agents_from_conversations(conn)
        print(f"    {updated} rows upserted")
    except Exception as exc:
        print(f"    [ERROR] {exc}")

    # Post-transform: update contacts.total_messages + total_conversations
    print(f"\n  [contacts] Enriching from messages...")
    try:
        with engine.begin() as conn:
            updated = update_contacts_from_messages(conn)
        print(f"    {updated} contacts enriched")
    except Exception as exc:
        print(f"    [ERROR] {exc}")

    # Post-transform: update agents.total_messages
    print(f"\n  [agents] Enriching total_messages from messages...")
    try:
        with engine.begin() as conn:
            updated = update_agents_messages(conn)
        print(f"    {updated} agents enriched")
    except Exception as exc:
        print(f"    [ERROR] {exc}")

    elapsed = time.time() - start

    print(f"\n{'=' * 60}")
    print(f"  Transform Summary")
    print(f"{'=' * 60}")
    print(f"  Elapsed: {elapsed:.1f}s\n")
    for entity, count in results.items():
        status = "OK" if count >= 0 else "ERROR"
        count_str = str(count) if count >= 0 else "FAILED"
        print(f"    {entity:<20s}  {count_str:>6s} rows  [{status}]")

    total_ok = sum(v for v in results.values() if v >= 0)
    total_err = sum(1 for v in results.values() if v < 0)
    print(f"\n  Total: {total_ok} rows upserted, {total_err} errors")
    print(f"{'=' * 60}")

    return 0 if total_err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
