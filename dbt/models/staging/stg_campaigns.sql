-- Staging: campaigns — deduplicate, coalesce nulls, recalculate rates.

with source as (
    select * from {{ source('raw', 'campaigns') }}
),

deduplicated as (
    select *,
        row_number() over (
            partition by tenant_id, campana_id
            order by total_enviados desc
        ) as _rn
    from source
),

cleaned as (
    select
        tenant_id,
        campana_id,
        campana_nombre,
        canal,
        proyecto_cuenta,
        tipo_campana,
        coalesce(total_enviados, 0) as total_enviados,
        coalesce(total_entregados, 0) as total_entregados,
        coalesce(total_clicks, 0) as total_clicks,
        coalesce(total_chunks, 0) as total_chunks,
        fecha_inicio,
        fecha_fin,
        coalesce(total_abiertos, 0) as total_abiertos,
        coalesce(total_rebotes, 0) as total_rebotes,
        coalesce(total_bloqueados, 0) as total_bloqueados,
        coalesce(total_spam, 0) as total_spam,
        coalesce(total_desuscritos, 0) as total_desuscritos,
        coalesce(total_conversiones, 0) as total_conversiones,

        -- Recalculate rates
        case when coalesce(total_enviados, 0) > 0
            then round(coalesce(total_clicks, 0)::numeric / total_enviados * 100, 2)
            else 0
        end as ctr,

        case when coalesce(total_enviados, 0) > 0
            then round(coalesce(total_entregados, 0)::numeric / total_enviados * 100, 2)
            else 0
        end as tasa_entrega,

        case when coalesce(total_entregados, 0) > 0
            then round(coalesce(total_abiertos, 0)::numeric / total_entregados * 100, 2)
            else 0
        end as open_rate,

        case when coalesce(total_clicks, 0) > 0
            then round(coalesce(total_conversiones, 0)::numeric / total_clicks * 100, 2)
            else 0
        end as conversion_rate

    from deduplicated
    where _rn = 1
)

select * from cleaned
