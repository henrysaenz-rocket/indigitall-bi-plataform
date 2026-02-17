-- Mart: fct_agent_performance — agent metrics computed from messages.
-- Replaces the static agents table with live calculations.

with messages as (
    select * from {{ ref('stg_messages') }}
    where agent_id is not null
)

select
    tenant_id,
    agent_id,
    count(*) as total_messages,
    count(distinct conversation_id) as conversations_handled,
    count(distinct contact_id) as unique_contacts,
    count(distinct date) as active_days,
    min(date) as first_active,
    max(date) as last_active,

    -- Timing
    avg(handle_time_seconds) filter (where handle_time_seconds is not null)
        as avg_handle_seconds,
    percentile_cont(0.5) within group (order by handle_time_seconds)
        filter (where handle_time_seconds is not null)
        as median_handle_seconds,
    avg(wait_time_seconds) filter (where wait_time_seconds is not null)
        as avg_wait_seconds,

    -- Quality
    count(*) filter (where is_fallback = true) as escalated_fallbacks,
    count(*) filter (where close_reason is not null) as closed_conversations

from messages
group by tenant_id, agent_id
order by tenant_id, total_messages desc
