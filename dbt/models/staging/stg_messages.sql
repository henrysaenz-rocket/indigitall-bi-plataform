-- Staging: messages — clean types, normalize direction values, deduplicate.
-- Materialized as view over raw.messages.

with source as (
    select * from {{ source('raw', 'messages') }}
),

deduplicated as (
    select *,
        row_number() over (
            partition by tenant_id, message_id
            order by timestamp desc
        ) as _rn
    from source
),

cleaned as (
    select
        tenant_id,
        message_id,
        timestamp,
        date,
        hour,
        day_of_week,
        send_type,

        -- Normalize direction values
        case
            when lower(direction) in ('inbound', 'entrante') then 'Inbound'
            when lower(direction) in ('bot') then 'Bot'
            when lower(direction) in ('agent', 'agente') then 'Agent'
            when lower(direction) in ('outbound', 'saliente') then 'Outbound'
            when lower(direction) in ('system', 'sistema') then 'System'
            else direction
        end as direction,

        content_type,
        status,
        contact_name,
        contact_id,
        conversation_id,
        agent_id,
        close_reason,
        intent,
        coalesce(is_fallback, false) as is_fallback,
        message_body,
        coalesce(is_bot, false) as is_bot,
        coalesce(is_human, false) as is_human,
        wait_time_seconds,
        handle_time_seconds

    from deduplicated
    where _rn = 1
)

select * from cleaned
