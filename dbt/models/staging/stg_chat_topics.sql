-- Staging: chat_topics — conversation topic categories.

with source as (
    select * from {{ source('raw', 'chat_topics') }}
),

deduplicated as (
    select
        tenant_id,
        topic_id,
        coalesce(topic_name, 'Sin nombre') as topic_name,
        description,
        is_active,
        row_number() over (
            partition by tenant_id, topic_id
            order by topic_id
        ) as _rn
    from source
    where topic_id is not null
)

select
    tenant_id,
    topic_id,
    topic_name,
    description,
    is_active
from deduplicated
where _rn = 1
