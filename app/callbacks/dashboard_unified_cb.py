"""Unified Dashboard callbacks — date range, KPIs, charts for all 7 tabs."""

from datetime import date, timedelta

from dash import Input, Output, State, callback, ctx, html, dcc
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

from app.services.data_service import DataService
from app.services.chart_service import ChartService
from app.services.contact_center_service import ContactCenterService
from app.services.toques_data_service import ToquesDataService


# ======================== Shared Helpers ========================

def _parse_range(date_range):
    if date_range:
        return (
            date.fromisoformat(str(date_range["start"])[:10]),
            date.fromisoformat(str(date_range["end"])[:10]),
        )
    today = date.today()
    return today - timedelta(days=29), today


def _kpi_card(label, value, icon, color="primary", md=3):
    display_value = f"{value:,}" if isinstance(value, int) else str(value)
    return dbc.Col(
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className=f"bi {icon} me-2 text-{color}"),
                    html.Span(label, className="kpi-label"),
                ]),
                html.Div(
                    html.Span(display_value, className="kpi-value"),
                    className="mt-1",
                ),
            ]),
        ], className="kpi-card"),
        md=md, sm=6, xs=12,
    )


# ======================== CB1: Date Selector ========================

@callback(
    Output("ud-date-store", "data"),
    Output("ud-date-picker", "style"),
    Output("ud-btn-7d", "active"),
    Output("ud-btn-30d", "active"),
    Output("ud-btn-90d", "active"),
    Output("ud-btn-custom", "active"),
    Input("ud-btn-7d", "n_clicks"),
    Input("ud-btn-30d", "n_clicks"),
    Input("ud-btn-90d", "n_clicks"),
    Input("ud-btn-custom", "n_clicks"),
    Input("ud-date-picker", "start_date"),
    Input("ud-date-picker", "end_date"),
)
def update_ud_date_range(_n7, _n30, _n90, _ncustom, picker_start, picker_end):
    triggered = ctx.triggered_id
    today = date.today()
    hide = {"display": "none"}
    show = {"display": "inline-block", "marginLeft": "12px"}

    if triggered == "ud-btn-7d":
        s = today - timedelta(days=6)
        return {"start": str(s), "end": str(today)}, hide, True, False, False, False
    if triggered == "ud-btn-90d":
        s = today - timedelta(days=89)
        return {"start": str(s), "end": str(today)}, hide, False, False, True, False
    if triggered == "ud-btn-custom":
        s = today - timedelta(days=29)
        return {"start": str(s), "end": str(today)}, show, False, False, False, True
    if triggered == "ud-date-picker" and picker_start and picker_end:
        return (
            {"start": str(picker_start)[:10], "end": str(picker_end)[:10]},
            show, False, False, False, True,
        )
    s = today - timedelta(days=29)
    return {"start": str(s), "end": str(today)}, hide, False, True, False, False


# ======================== Tab: Control Toques ========================

@callback(
    Output("ud-tq-kpi-row", "children"),
    Input("ud-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_ud_tq_kpis(date_range, tenant):
    svc = DataService()
    start, end = _parse_range(date_range)
    kpis = svc.get_toques_kpis(tenant_filter=tenant, start_date=start, end_date=end)
    return [
        _kpi_card("% Sobre-tocados", f"{kpis['pct_over_touched']}%",
                  "bi-exclamation-octagon", "danger"),
        _kpi_card("Sobre-tocados", kpis["over_touched"],
                  "bi-bell-exclamation", "warning"),
        _kpi_card("Contacto/Semanas", kpis["total_contact_weeks"],
                  "bi-calendar-week", "info"),
        _kpi_card("Prom Msgs/Sem", f"{kpis['avg_msgs_per_contact_week']}",
                  "bi-graph-up", "primary"),
    ]


@callback(
    Output("ud-tq-distribution-chart", "figure"),
    Input("ud-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_ud_tq_distribution(date_range, tenant):
    svc, charts = DataService(), ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_toques_distribution(tenant_filter=tenant, start_date=start, end_date=end)
    if df.empty:
        return charts._create_empty_chart("Distribucion de Toques")
    return charts.create_bar_chart(df, "", "bucket", "count")


@callback(
    Output("ud-tq-trend-chart", "figure"),
    Input("ud-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_ud_tq_trend(date_range, tenant):
    svc, charts = DataService(), ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_toques_weekly_trend(tenant_filter=tenant, start_date=start, end_date=end)
    if df.empty or "pct_over_touched" not in df.columns:
        return charts._create_empty_chart("Tendencia Semanal")
    return charts.create_chart(df, "line", "", "week", "pct_over_touched")


@callback(
    Output("ud-tq-contacts-table", "data"),
    Output("ud-tq-contacts-table", "columns"),
    Input("ud-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_ud_tq_contacts(date_range, tenant):
    svc = DataService()
    start, end = _parse_range(date_range)
    df = svc.get_over_touched_contacts(tenant_filter=tenant, start_date=start, end_date=end)
    if df.empty:
        return [], []
    col_map = {
        "contact_id": "ID Contacto", "contact_name": "Contacto",
        "semana": "Semana", "mensajes": "Mensajes",
    }
    available = [c for c in col_map if c in df.columns]
    columns = [{"name": col_map[c], "id": c} for c in available]
    return df[available].to_dict("records"), columns


@callback(
    Output("ud-tq-download-csv", "data"),
    Input("ud-tq-export-csv-btn", "n_clicks"),
    State("ud-date-store", "data"),
    State("tenant-context", "data"),
    prevent_initial_call=True,
)
def export_ud_tq_csv(n_clicks, date_range, tenant):
    if not n_clicks:
        raise PreventUpdate
    svc = DataService()
    start, end = _parse_range(date_range)
    df = svc.get_over_touched_contacts(
        tenant_filter=tenant, start_date=start, end_date=end, limit=5000,
    )
    if df.empty:
        raise PreventUpdate
    return dcc.send_data_frame(df.to_csv, "contactos_sobre_tocados.csv", index=False)


# ======================== Tab: SMS ========================

@callback(
    Output("ud-sms-kpi-row", "children"),
    Input("ud-date-store", "data"),
)
def load_ud_sms_kpis(date_range):
    svc = ToquesDataService()
    start, end = _parse_range(date_range)
    kpis = svc.get_kpis(channels=["SMS"], start_date=start, end_date=end)
    return [
        _kpi_card("Total Enviados", kpis["total_enviados"], "bi-send"),
        _kpi_card("Total Clicks", kpis["total_clicks"], "bi-cursor"),
        _kpi_card("CTR Promedio", f"{kpis['ctr_promedio']}%", "bi-percent", "success"),
        _kpi_card("Total Chunks", kpis["total_chunks"], "bi-stack"),
    ]


@callback(
    Output("ud-sms-sends-chunks-chart", "figure"),
    Input("ud-date-store", "data"),
)
def load_ud_sms_sends_chunks(date_range):
    svc, charts = ToquesDataService(), ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_sends_vs_chunks(channels=["SMS"], start_date=start, end_date=end)
    if df.empty:
        return charts._create_empty_chart("Enviados vs Chunks")
    return charts.create_multi_line_chart(
        df, "", "date", ["enviados", "chunks"],
        {"enviados": "Enviados", "chunks": "Chunks"},
    )


@callback(
    Output("ud-sms-sends-clicks-chart", "figure"),
    Input("ud-date-store", "data"),
)
def load_ud_sms_sends_clicks(date_range):
    svc, charts = ToquesDataService(), ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_sends_clicks_ctr(channels=["SMS"], start_date=start, end_date=end)
    if df.empty:
        return charts._create_empty_chart("Enviados vs Clicks vs CTR")
    return charts.create_combo_chart(
        df, "", "date",
        y1_cols=["enviados", "clicks"],
        y1_labels={"enviados": "Enviados", "clicks": "Clicks"},
        y2_cols=["ctr"],
        y2_labels={"ctr": "CTR %"},
    )


@callback(
    Output("ud-sms-heatmap-chart", "figure"),
    Input("ud-date-store", "data"),
)
def load_ud_sms_heatmap(date_range):
    svc, charts = ToquesDataService(), ChartService()
    df = svc.get_heatmap_data(channels=["SMS"])
    if df.empty:
        return charts._create_empty_chart("Mapa de Calor SMS")
    return charts.create_heatmap(df, "", "hora", "dia_semana", "value")


@callback(
    Output("ud-sms-ranking-chart", "figure"),
    Input("ud-date-store", "data"),
)
def load_ud_sms_ranking(date_range):
    svc, charts = ToquesDataService(), ChartService()
    df = svc.get_campaigns_by_volume(channels=["SMS"], limit=10)
    if df.empty:
        return charts._create_empty_chart("Sin datos de campanas")
    return charts.create_ranking_bar_chart(
        df, "", "campana_nombre", "total_enviados", secondary_col="ctr",
    )


# ======================== Tab: Email ========================

@callback(
    Output("ud-email-kpi-row", "children"),
    Input("ud-date-store", "data"),
)
def load_ud_email_kpis(date_range):
    svc = ToquesDataService()
    start, end = _parse_range(date_range)
    kpis = svc.get_email_kpis(start_date=start, end_date=end)
    return [
        _kpi_card("% Open Rate", f"{kpis['open_rate']}%", "bi-envelope-open", "primary", md=2),
        _kpi_card("% CTR", f"{kpis['ctr']}%", "bi-cursor", "success", md=2),
        _kpi_card("% Rebotes", f"{kpis['pct_rebotes']}%", "bi-exclamation-triangle", "warning", md=2),
        _kpi_card("% Bloqueados", f"{kpis['pct_bloqueados']}%", "bi-slash-circle", "danger", md=2),
        _kpi_card("% Spam", f"{kpis['pct_spam']}%", "bi-shield-exclamation", "danger", md=2),
        _kpi_card("% Desuscritos", f"{kpis['pct_desuscritos']}%", "bi-person-dash", "warning", md=2),
    ]


@callback(
    Output("ud-email-engagement-chart", "figure"),
    Input("ud-date-store", "data"),
)
def load_ud_email_engagement(date_range):
    svc, charts = ToquesDataService(), ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_email_engagement_trend(start_date=start, end_date=end)
    if df.empty:
        return charts._create_empty_chart("Engagement Email")
    return charts.create_multi_line_chart(
        df, "", "date", ["entregados", "abiertos", "clicks"],
        {"entregados": "Entregados", "abiertos": "Abiertos", "clicks": "Clicks"},
    )


@callback(
    Output("ud-email-errors-chart", "figure"),
    Input("ud-date-store", "data"),
)
def load_ud_email_errors(date_range):
    svc, charts = ToquesDataService(), ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_email_error_breakdown(start_date=start, end_date=end)
    if df.empty or df["cantidad"].sum() == 0:
        return charts._create_empty_chart("Desglose de Errores")
    return charts.create_bar_chart(df, "", "tipo", "cantidad")


@callback(
    Output("ud-email-heatmap-chart", "figure"),
    Input("ud-date-store", "data"),
)
def load_ud_email_heatmap(date_range):
    svc, charts = ToquesDataService(), ChartService()
    df = svc.get_heatmap_data(channels=["Email"])
    if df.empty:
        return charts._create_empty_chart("Mapa de Calor Email")
    return charts.create_heatmap(df, "", "hora", "dia_semana", "value")


@callback(
    Output("ud-email-ranking-chart", "figure"),
    Input("ud-date-store", "data"),
)
def load_ud_email_ranking(date_range):
    svc, charts = ToquesDataService(), ChartService()
    df = svc.get_email_campaigns_by_engagement(limit=10)
    if df.empty:
        return charts._create_empty_chart("Sin datos de campanas")
    return charts.create_ranking_bar_chart(
        df, "", "campana_nombre", "open_rate", secondary_col="ctr",
    )


# ======================== Tab: Push ========================

@callback(
    Output("ud-push-kpi-row", "children"),
    Input("ud-date-store", "data"),
)
def load_ud_push_kpis(date_range):
    svc = ToquesDataService()
    start, end = _parse_range(date_range)
    kpis = svc.get_kpis(channels=["Push"], start_date=start, end_date=end)
    env = kpis["total_enviados"]
    chunks = kpis["total_chunks"]
    tasa_entrega = round(chunks / env * 100, 2) if env > 0 else 0
    return [
        _kpi_card("Total Enviados", env, "bi-send"),
        _kpi_card("Total Entregados", chunks, "bi-check2-circle", "success"),
        _kpi_card("CTR", f"{kpis['ctr_promedio']}%", "bi-cursor", "primary"),
        _kpi_card("Tasa Entrega", f"{tasa_entrega}%", "bi-arrow-right-circle", "info"),
    ]


@callback(
    Output("ud-push-trend-chart", "figure"),
    Input("ud-date-store", "data"),
)
def load_ud_push_trend(date_range):
    svc, charts = ToquesDataService(), ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_sends_clicks_ctr(channels=["Push"], start_date=start, end_date=end)
    if df.empty:
        return charts._create_empty_chart("Enviados vs Clicks Push")
    return charts.create_combo_chart(
        df, "", "date",
        y1_cols=["enviados", "clicks"],
        y1_labels={"enviados": "Enviados", "clicks": "Clicks"},
        y2_cols=["ctr"],
        y2_labels={"ctr": "CTR %"},
    )


@callback(
    Output("ud-push-heatmap-chart", "figure"),
    Input("ud-date-store", "data"),
)
def load_ud_push_heatmap(date_range):
    svc, charts = ToquesDataService(), ChartService()
    df = svc.get_heatmap_data(channels=["Push"])
    if df.empty:
        return charts._create_empty_chart("Mapa de Calor Push")
    return charts.create_heatmap(df, "", "hora", "dia_semana", "value")


# ======================== Tab: In App/Web ========================

@callback(
    Output("ud-inapp-kpi-row", "children"),
    Input("ud-date-store", "data"),
)
def load_ud_inapp_kpis(date_range):
    svc = ToquesDataService()
    start, end = _parse_range(date_range)
    kpis = svc.get_inapp_kpis(start_date=start, end_date=end)
    return [
        _kpi_card("Impresiones", kpis["total_impresiones"], "bi-eye"),
        _kpi_card("Clicks", kpis["total_clicks"], "bi-cursor", "primary"),
        _kpi_card("CTR", f"{kpis['ctr']}%", "bi-percent", "success"),
        _kpi_card("Conversiones", kpis["total_conversiones"], "bi-trophy", "warning"),
    ]


@callback(
    Output("ud-inapp-engagement-chart", "figure"),
    Input("ud-date-store", "data"),
)
def load_ud_inapp_engagement(date_range):
    svc, charts = ToquesDataService(), ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_inapp_engagement_trend(start_date=start, end_date=end)
    if df.empty:
        return charts._create_empty_chart("Impresiones vs Clicks")
    return charts.create_multi_line_chart(
        df, "", "date", ["impresiones", "clicks"],
        {"impresiones": "Impresiones", "clicks": "Clicks"},
    )


@callback(
    Output("ud-inapp-funnel-chart", "figure"),
    Input("ud-date-store", "data"),
)
def load_ud_inapp_funnel(date_range):
    svc, charts = ToquesDataService(), ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_inapp_conversion_funnel(start_date=start, end_date=end)
    if df.empty or df["cantidad"].sum() == 0:
        return charts._create_empty_chart("Funnel de Conversion")
    return charts.create_bar_chart(df, "", "etapa", "cantidad")


# ======================== Tab: Contact Center ========================

@callback(
    Output("ud-cc-kpi-row", "children"),
    Input("ud-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_ud_cc_kpis(date_range, tenant):
    svc = ContactCenterService()
    start, end = _parse_range(date_range)
    kpis = svc.get_cc_kpis(tenant_filter=tenant, start_date=start, end_date=end)
    return [
        _kpi_card("Total Conversaciones", kpis["total_conversations"], "bi-chat-square-dots"),
        _kpi_card("Agentes Activos", kpis["active_agents"], "bi-people"),
        _kpi_card("T. Espera Prom", f"{kpis['avg_wait_minutes']} min", "bi-clock"),
        _kpi_card("T. Gestion Prom", f"{kpis['avg_handle_minutes']} min", "bi-stopwatch"),
    ]


@callback(
    Output("ud-cc-conv-trend-chart", "figure"),
    Input("ud-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_ud_cc_conv_trend(date_range, tenant):
    svc, charts = ContactCenterService(), ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_conversations_over_time(tenant_filter=tenant, start_date=start, end_date=end)
    if df.empty:
        return charts._create_empty_chart("Conversaciones por Dia")
    return charts.create_chart(df, "area", "", "date", "count")


@callback(
    Output("ud-cc-wait-chart", "figure"),
    Input("ud-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_ud_cc_wait(date_range, tenant):
    svc, charts = ContactCenterService(), ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_wait_time_distribution(tenant_filter=tenant, start_date=start, end_date=end)
    if df.empty:
        return charts._create_empty_chart("Distribucion de Espera")
    return charts.create_bar_chart(df, "", "bucket", "count")


@callback(
    Output("ud-cc-agent-table", "data"),
    Output("ud-cc-agent-table", "columns"),
    Input("ud-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_ud_cc_agent_table(date_range, tenant):
    svc = ContactCenterService()
    start, end = _parse_range(date_range)
    df = svc.get_conversations_by_agent(tenant_filter=tenant, start_date=start, end_date=end)
    if df.empty:
        return [], []
    col_map = {
        "agent_id": "Agente", "conversations": "Conversaciones",
        "contacts": "Contactos",
    }
    columns = [{"name": col_map.get(c, c), "id": c} for c in df.columns if c in col_map]
    return df.to_dict("records"), columns


@callback(
    Output("ud-cc-close-reasons-chart", "figure"),
    Input("ud-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_ud_cc_close_reasons(date_range, tenant):
    svc, charts = ContactCenterService(), ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_close_reasons(tenant_filter=tenant, start_date=start, end_date=end)
    if df.empty:
        return charts._create_empty_chart("Razones de Cierre")
    return charts._create_horizontal_bar_chart(df, "", "reason", "count")


@callback(
    Output("ud-cc-hourly-chart", "figure"),
    Input("ud-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_ud_cc_hourly(date_range, tenant):
    svc, charts = ContactCenterService(), ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_hourly_queue(tenant_filter=tenant, start_date=start, end_date=end)
    if df.empty:
        return charts._create_empty_chart("Conversaciones por Hora")
    return charts.create_hourly_distribution_chart(df)


# ======================== Tab: Bot ========================

@callback(
    Output("ud-bot-kpi-row", "children"),
    Input("ud-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_ud_bot_kpis(date_range, tenant):
    svc = DataService()
    start, end = _parse_range(date_range)
    stats = svc.get_summary_stats_for_period(
        tenant_filter=tenant, start_date=start, end_date=end,
    )
    resolution = svc.get_bot_resolution_summary(
        tenant_filter=tenant, start_date=start, end_date=end,
    )
    bot_msgs, human_msgs = 0, 0
    if not resolution.empty:
        bot_row = resolution[resolution["category"] == "Bot"]
        human_row = resolution[resolution["category"] == "Agente"]
        bot_msgs = int(bot_row["count"].iloc[0]) if not bot_row.empty else 0
        human_msgs = int(human_row["count"].iloc[0]) if not human_row.empty else 0

    return [
        _kpi_card("Tasa Fallback", f"{stats['fallback_rate']}%",
                  "bi-exclamation-triangle", "warning", md=4),
        _kpi_card("Mensajes Bot", bot_msgs, "bi-robot", "primary", md=4),
        _kpi_card("Mensajes Agente", human_msgs, "bi-person", "success", md=4),
    ]


@callback(
    Output("ud-bot-vs-human-chart", "figure"),
    Input("ud-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_ud_bot_vs_human(date_range, tenant):
    svc, charts = DataService(), ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_bot_resolution_summary(
        tenant_filter=tenant, start_date=start, end_date=end,
    )
    if df.empty:
        return charts._create_empty_chart("Bot vs Agente")
    return charts.create_pie_chart(df, "", "category", "count")


@callback(
    Output("ud-bot-fallback-chart", "figure"),
    Input("ud-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_ud_bot_fallback_trend(date_range, tenant):
    svc, charts = DataService(), ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_fallback_trend_filtered(
        tenant_filter=tenant, start_date=start, end_date=end,
    )
    if df.empty or "fallback_rate" not in df.columns:
        return charts._create_empty_chart("Tendencia Fallback")
    return charts.create_chart(df, "line", "", "date", "fallback_rate")


@callback(
    Output("ud-bot-intents-chart", "figure"),
    Input("ud-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_ud_bot_intents(date_range, tenant):
    svc, charts = DataService(), ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_top_intents_filtered(
        tenant_filter=tenant, start_date=start, end_date=end, limit=10,
    )
    return charts.create_intent_chart(df)


@callback(
    Output("ud-bot-content-chart", "figure"),
    Input("ud-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_ud_bot_content_types(date_range, tenant):
    svc, charts = DataService(), ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_content_type_breakdown(
        tenant_filter=tenant, start_date=start, end_date=end,
    )
    if df.empty:
        return charts._create_empty_chart("Tipos de Contenido")
    return charts.create_pie_chart(df, "", "content_type", "count")
