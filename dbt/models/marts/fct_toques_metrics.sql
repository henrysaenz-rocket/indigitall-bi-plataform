-- Mart: fct_toques_metrics — campaign channel metrics aggregated by period.
-- Powers the Dashboard page tabs (SMS+WhatsApp, Email, In-App/Web).

with toques as (
    select * from {{ ref('stg_toques_daily') }}
)

select
    tenant_id,
    canal,
    proyecto_cuenta,

    -- Monthly aggregation
    date_trunc('month', date)::date as month,

    -- Volume
    sum(enviados) as total_enviados,
    sum(entregados) as total_entregados,
    sum(clicks) as total_clicks,
    sum(chunks) as total_chunks,
    sum(usuarios_unicos) as total_usuarios_unicos,

    -- Email-specific
    sum(abiertos) as total_abiertos,
    sum(rebotes) as total_rebotes,
    sum(bloqueados) as total_bloqueados,
    sum(spam) as total_spam,
    sum(desuscritos) as total_desuscritos,
    sum(conversiones) as total_conversiones,

    -- Rates (calculated from sums)
    case when sum(enviados) > 0
        then round(sum(clicks)::numeric / sum(enviados) * 100, 2)
        else 0
    end as ctr,

    case when sum(enviados) > 0
        then round(sum(entregados)::numeric / sum(enviados) * 100, 2)
        else 0
    end as tasa_entrega,

    case when sum(entregados) > 0
        then round(sum(abiertos)::numeric / sum(entregados) * 100, 2)
        else 0
    end as open_rate,

    case when sum(clicks) > 0
        then round(sum(conversiones)::numeric / sum(clicks) * 100, 2)
        else 0
    end as conversion_rate,

    -- Counts
    count(distinct date) as active_days

from toques
group by tenant_id, canal, proyecto_cuenta, date_trunc('month', date)
order by tenant_id, canal, month
