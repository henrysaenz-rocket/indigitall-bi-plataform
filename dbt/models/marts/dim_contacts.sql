-- Mart: dim_contacts — enriched contact dimension from messages.
-- Recalculates totals from the messages fact table for accuracy.

with contacts as (
    select * from {{ ref('stg_contacts') }}
),

message_stats as (
    select
        tenant_id,
        contact_id,
        contact_name,
        count(*) as total_messages,
        count(distinct conversation_id) as total_conversations,
        min(date) as first_contact,
        max(date) as last_contact,
        count(*) filter (where is_fallback = true) as fallback_messages,
        count(distinct date) as active_days
    from {{ ref('stg_messages') }}
    where contact_id is not null
    group by tenant_id, contact_id, contact_name
)

select
    coalesce(ms.tenant_id, c.tenant_id) as tenant_id,
    coalesce(ms.contact_id, c.contact_id) as contact_id,
    coalesce(ms.contact_name, c.contact_name) as contact_name,
    coalesce(ms.total_messages, c.total_messages) as total_messages,
    coalesce(ms.total_conversations, c.total_conversations) as total_conversations,
    coalesce(ms.first_contact, c.first_contact) as first_contact,
    coalesce(ms.last_contact, c.last_contact) as last_contact,
    coalesce(ms.fallback_messages, 0) as fallback_messages,
    coalesce(ms.active_days, 0) as active_days

from message_stats ms
full outer join contacts c
    on ms.tenant_id = c.tenant_id and ms.contact_id = c.contact_id
