-- Staging: contacts — deduplicate, ensure non-null totals.

with source as (
    select * from {{ source('raw', 'contacts') }}
),

deduplicated as (
    select *,
        row_number() over (
            partition by tenant_id, contact_id
            order by last_contact desc nulls last
        ) as _rn
    from source
),

cleaned as (
    select
        tenant_id,
        contact_id,
        contact_name,
        coalesce(total_messages, 0) as total_messages,
        first_contact,
        last_contact,
        coalesce(total_conversations, 0) as total_conversations
    from deduplicated
    where _rn = 1
)

select * from cleaned
