-- Mart: dim_campaigns — campaign dimension with aggregated daily data.
-- Combines campaign metadata with computed totals from toques_daily.

with campaigns as (
    select * from {{ ref('stg_campaigns') }}
),

daily_totals as (
    select
        tenant_id,
        canal,
        proyecto_cuenta,
        sum(enviados) as daily_total_enviados,
        sum(clicks) as daily_total_clicks,
        sum(conversiones) as daily_total_conversiones,
        count(distinct date) as active_days,
        min(date) as first_send_date,
        max(date) as last_send_date
    from {{ ref('stg_toques_daily') }}
    group by tenant_id, canal, proyecto_cuenta
)

select
    c.tenant_id,
    c.campana_id,
    c.campana_nombre,
    c.canal,
    c.proyecto_cuenta,
    c.tipo_campana,
    c.total_enviados,
    c.total_entregados,
    c.total_clicks,
    c.total_chunks,
    c.fecha_inicio,
    c.fecha_fin,
    c.total_abiertos,
    c.total_rebotes,
    c.total_bloqueados,
    c.total_spam,
    c.total_desuscritos,
    c.total_conversiones,
    c.ctr,
    c.tasa_entrega,
    c.open_rate,
    c.conversion_rate,
    coalesce(d.active_days, 0) as active_days,
    d.first_send_date,
    d.last_send_date

from campaigns c
left join daily_totals d
    on c.tenant_id = d.tenant_id
    and c.canal = d.canal
    and c.proyecto_cuenta = d.proyecto_cuenta
