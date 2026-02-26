-- Mart: fct_agent_performance — agent metrics from messages + conversations.
-- Replaces the static agents table with live calculations.
-- Timing metrics now come from chat_conversations (more accurate than messages).

with messages as (
    select * from {{ ref('stg_messages') }}
    where agent_id is not null
),

conversations as (
    select * from {{ ref('stg_chat_conversations') }}
    where agent_id is not null
),

msg_stats as (
    select
        tenant_id,
        agent_id,
        count(*) as total_messages,
        count(distinct conversation_id) as msg_conversations,
        count(distinct contact_id) as unique_contacts,
        count(distinct date) as active_days,
        min(date) as first_active,
        max(date) as last_active,
        count(*) filter (where is_fallback = true) as escalated_fallbacks,
        count(*) filter (where close_reason is not null) as closed_conversations
    from messages
    group by tenant_id, agent_id
),

conv_stats as (
    select
        tenant_id,
        agent_id,
        count(*) as conversations_handled,
        avg(wait_time_seconds) filter (where wait_time_seconds is not null)
            as avg_wait_seconds,
        avg(handle_time_seconds) filter (where handle_time_seconds is not null)
            as avg_handle_seconds,
        percentile_cont(0.5) within group (order by handle_time_seconds)
            filter (where handle_time_seconds is not null)
            as median_handle_seconds,
        avg(total_duration_seconds) filter (where total_duration_seconds is not null)
            as avg_total_duration_seconds
    from conversations
    group by tenant_id, agent_id
)

select
    m.tenant_id,
    m.agent_id,
    m.total_messages,
    coalesce(c.conversations_handled, m.msg_conversations) as conversations_handled,
    m.unique_contacts,
    m.active_days,
    m.first_active,
    m.last_active,

    -- Timing: prefer conversation-level metrics, fall back to message-level
    coalesce(c.avg_handle_seconds, 0)::int as avg_handle_seconds,
    coalesce(c.median_handle_seconds, 0)::int as median_handle_seconds,
    coalesce(c.avg_wait_seconds, 0)::int as avg_wait_seconds,
    coalesce(c.avg_total_duration_seconds, 0)::int as avg_total_duration_seconds,

    -- Quality
    m.escalated_fallbacks,
    m.closed_conversations

from msg_stats m
left join conv_stats c
    on m.tenant_id = c.tenant_id and m.agent_id = c.agent_id
order by m.tenant_id, m.total_messages desc
