-- Staging: chat_conversations — cleaned timing, computed duration.

with source as (
    select * from {{ source('raw', 'chat_conversations') }}
),

cleaned as (
    select
        tenant_id,
        session_id,
        conversation_session_id,
        contact_id,
        agent_id,
        agent_email,
        channel,
        queued_at,
        assigned_at,
        closed_at,
        initial_session_id,

        -- Clean negative timing → NULL
        case when wait_time_seconds >= 0 then wait_time_seconds else null end
            as wait_time_seconds,
        case when handle_time_seconds >= 0 then handle_time_seconds else null end
            as handle_time_seconds,

        -- Compute total duration (closed_at - queued_at) in seconds
        case
            when closed_at is not null and queued_at is not null
                 and extract(epoch from (closed_at - queued_at)) >= 0
            then extract(epoch from (closed_at - queued_at))::int
            else null
        end as total_duration_seconds

    from source
    where session_id is not null
)

select * from cleaned
