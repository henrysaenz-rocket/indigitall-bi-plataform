-- Staging: agents — deduplicate, ensure non-null totals.

with source as (
    select * from {{ source('raw', 'agents') }}
),

deduplicated as (
    select *,
        row_number() over (
            partition by tenant_id, agent_id
            order by total_messages desc
        ) as _rn
    from source
),

cleaned as (
    select
        tenant_id,
        agent_id,
        coalesce(total_messages, 0) as total_messages,
        coalesce(conversations_handled, 0) as conversations_handled,
        avg_handle_time_seconds
    from deduplicated
    where _rn = 1
)

select * from cleaned
