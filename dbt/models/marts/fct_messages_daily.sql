-- Mart: fct_messages_daily — daily message aggregations per tenant.
-- Pre-computed to power the home page KPIs and trend charts.

with messages as (
    select * from {{ ref('stg_messages') }}
)

select
    tenant_id,
    date,

    -- Volume
    count(*) as total_messages,
    count(distinct contact_id) as unique_contacts,
    count(distinct conversation_id) as conversations,
    count(distinct agent_id) filter (where agent_id is not null) as active_agents,

    -- Direction breakdown
    count(*) filter (where direction = 'Inbound') as inbound_count,
    count(*) filter (where direction = 'Bot') as bot_count,
    count(*) filter (where direction = 'Agent') as agent_count,

    -- Fallback
    count(*) filter (where is_fallback = true) as fallback_count,
    case when count(*) > 0
        then round(count(*) filter (where is_fallback = true)::numeric / count(*) * 100, 2)
        else 0
    end as fallback_rate,

    -- Timing
    avg(wait_time_seconds) filter (where wait_time_seconds is not null) as avg_wait_seconds,
    avg(handle_time_seconds) filter (where handle_time_seconds is not null) as avg_handle_seconds

from messages
group by tenant_id, date
order by tenant_id, date
