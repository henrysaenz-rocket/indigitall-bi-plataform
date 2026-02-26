-- Validates that conversation timing metrics are non-negative.
-- Returns rows that FAIL the check (0 rows = pass).

select
    tenant_id,
    session_id,
    wait_time_seconds,
    handle_time_seconds
from {{ source('raw', 'chat_conversations') }}
where wait_time_seconds < 0
   or handle_time_seconds < 0
