-- Validates that all messages have a recognized direction value.
-- Returns rows that FAIL the check (0 rows = pass).

select
    tenant_id,
    message_id,
    direction
from {{ source('raw', 'messages') }}
where direction not in ('Inbound', 'Bot', 'Agent', 'Outbound', 'System')
