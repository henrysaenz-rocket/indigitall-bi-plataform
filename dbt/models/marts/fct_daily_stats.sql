-- Mart: fct_daily_stats — combined daily KPIs from messages + campaigns.
-- Single row per tenant per date for dashboard overview.

with msg_daily as (
    select * from {{ ref('fct_messages_daily') }}
),

toques_daily as (
    select
        tenant_id,
        date,
        sum(enviados) as total_enviados,
        sum(entregados) as total_entregados,
        sum(clicks) as total_clicks,
        sum(conversiones) as total_conversiones,
        case when sum(enviados) > 0
            then round(sum(clicks)::numeric / sum(enviados) * 100, 2)
            else 0
        end as avg_ctr
    from {{ ref('stg_toques_daily') }}
    group by tenant_id, date
)

select
    coalesce(m.tenant_id, t.tenant_id) as tenant_id,
    coalesce(m.date, t.date) as date,

    -- Messages
    coalesce(m.total_messages, 0) as total_messages,
    coalesce(m.unique_contacts, 0) as unique_contacts,
    coalesce(m.conversations, 0) as conversations,
    coalesce(m.active_agents, 0) as active_agents,
    coalesce(m.fallback_count, 0) as fallback_count,
    coalesce(m.fallback_rate, 0) as fallback_rate,
    coalesce(m.avg_wait_seconds, 0) as avg_wait_seconds,
    coalesce(m.avg_handle_seconds, 0) as avg_handle_seconds,

    -- Campaigns
    coalesce(t.total_enviados, 0) as total_enviados,
    coalesce(t.total_entregados, 0) as total_entregados,
    coalesce(t.total_clicks, 0) as total_clicks,
    coalesce(t.total_conversiones, 0) as total_conversiones,
    coalesce(t.avg_ctr, 0) as avg_ctr

from msg_daily m
full outer join toques_daily t
    on m.tenant_id = t.tenant_id and m.date = t.date
order by 1, 2
