-- Validates that no messages have a date in the future.
-- Returns rows that FAIL the check (0 rows = pass).

select
    tenant_id,
    message_id,
    date
from {{ source('raw', 'messages') }}
where date > current_date
