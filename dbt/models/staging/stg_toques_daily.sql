-- Staging: toques_daily — deduplicate, coalesce nulls, recalculate rates.

with source as (
    select * from {{ source('raw', 'toques_daily') }}
),

deduplicated as (
    select *,
        row_number() over (
            partition by tenant_id, date, canal, proyecto_cuenta
            order by enviados desc
        ) as _rn
    from source
),

cleaned as (
    select
        tenant_id,
        date,
        canal,
        proyecto_cuenta,
        coalesce(enviados, 0) as enviados,
        coalesce(entregados, 0) as entregados,
        coalesce(clicks, 0) as clicks,
        coalesce(chunks, 0) as chunks,
        coalesce(usuarios_unicos, 0) as usuarios_unicos,
        coalesce(abiertos, 0) as abiertos,
        coalesce(rebotes, 0) as rebotes,
        coalesce(bloqueados, 0) as bloqueados,
        coalesce(spam, 0) as spam,
        coalesce(desuscritos, 0) as desuscritos,
        coalesce(conversiones, 0) as conversiones,

        -- Recalculate rates from raw counts (more reliable than stored rates)
        case when coalesce(enviados, 0) > 0
            then round(coalesce(clicks, 0)::numeric / enviados * 100, 2)
            else 0
        end as ctr,

        case when coalesce(enviados, 0) > 0
            then round(coalesce(entregados, 0)::numeric / enviados * 100, 2)
            else 0
        end as tasa_entrega,

        case when coalesce(entregados, 0) > 0
            then round(coalesce(abiertos, 0)::numeric / entregados * 100, 2)
            else 0
        end as open_rate,

        case when coalesce(clicks, 0) > 0
            then round(coalesce(conversiones, 0)::numeric / clicks * 100, 2)
            else 0
        end as conversion_rate

    from deduplicated
    where _rn = 1
)

select * from cleaned
