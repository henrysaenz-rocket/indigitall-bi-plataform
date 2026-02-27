"""Contact Center dashboard callbacks — date range, KPIs, charts, agent table."""

from datetime import date, timedelta

from dash import Input, Output, callback, ctx, html
import dash_bootstrap_components as dbc
import plotly.express as px

from app.services.contact_center_service import ContactCenterService
from app.services.chart_service import ChartService

CHART_COLORS = ["#1E88E5", "#76C043", "#A0A3BD", "#42A5F5", "#1565C0", "#FFC107", "#9C27B0", "#FF5722"]


def _parse_range(date_range):
    if date_range:
        return (
            date.fromisoformat(str(date_range["start"])[:10]),
            date.fromisoformat(str(date_range["end"])[:10]),
        )
    today = date.today()
    return today - timedelta(days=29), today


def _kpi_card(label, value, icon, color="primary"):
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
        md=3, sm=6, xs=12,
    )


# -- CB1: Date range selector -----------------------------------------------

@callback(
    Output("cc-date-store", "data"),
    Output("cc-date-picker", "style"),
    Output("cc-btn-7d", "active"),
    Output("cc-btn-30d", "active"),
    Output("cc-btn-90d", "active"),
    Output("cc-btn-custom", "active"),
    Input("cc-btn-7d", "n_clicks"),
    Input("cc-btn-30d", "n_clicks"),
    Input("cc-btn-90d", "n_clicks"),
    Input("cc-btn-custom", "n_clicks"),
    Input("cc-date-picker", "start_date"),
    Input("cc-date-picker", "end_date"),
)
def update_cc_date_range(_n7, _n30, _n90, _ncustom, picker_start, picker_end):
    triggered = ctx.triggered_id
    today = date.today()
    hide = {"display": "none"}
    show = {"display": "inline-block", "marginLeft": "12px"}

    if triggered == "cc-btn-7d":
        s = today - timedelta(days=6)
        return {"start": str(s), "end": str(today)}, hide, True, False, False, False
    if triggered == "cc-btn-90d":
        s = today - timedelta(days=89)
        return {"start": str(s), "end": str(today)}, hide, False, False, True, False
    if triggered == "cc-btn-custom":
        s = today - timedelta(days=29)
        return {"start": str(s), "end": str(today)}, show, False, False, False, True
    if triggered == "cc-date-picker" and picker_start and picker_end:
        return (
            {"start": str(picker_start)[:10], "end": str(picker_end)[:10]},
            show, False, False, False, True,
        )
    s = today - timedelta(days=29)
    return {"start": str(s), "end": str(today)}, hide, False, True, False, False


# -- CB2: KPI cards ----------------------------------------------------------

@callback(
    Output("cc-kpi-row", "children"),
    Input("cc-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_cc_kpis(date_range, tenant):
    svc = ContactCenterService()
    start, end = _parse_range(date_range)
    kpis = svc.get_cc_kpis(tenant_filter=tenant, start_date=start, end_date=end)
    return [
        _kpi_card("Total Conversaciones", kpis["total_conversations"], "bi-chat-square-dots"),
        _kpi_card("Agentes Activos", kpis["active_agents"], "bi-people"),
        _kpi_card("T. Espera Prom", f"{kpis['avg_wait_minutes']} min", "bi-clock"),
        _kpi_card("T. Gestion Prom", f"{kpis['avg_handle_minutes']} min", "bi-stopwatch"),
    ]


# -- CB3: Conversations over time --------------------------------------------

@callback(
    Output("cc-conv-trend-chart", "figure"),
    Input("cc-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_cc_conv_trend(date_range, tenant):
    svc = ContactCenterService()
    charts = ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_conversations_over_time(tenant_filter=tenant, start_date=start, end_date=end)
    if df.empty:
        return charts._create_empty_chart("Conversaciones por Dia")
    return charts.create_chart(df, "area", "", "date", "count")


# -- CB4: Wait time distribution ---------------------------------------------

@callback(
    Output("cc-wait-distribution-chart", "figure"),
    Input("cc-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_cc_wait_distribution(date_range, tenant):
    svc = ContactCenterService()
    charts = ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_wait_time_distribution(tenant_filter=tenant, start_date=start, end_date=end)
    if df.empty:
        return charts._create_empty_chart("Distribucion de Espera")
    return charts.create_bar_chart(df, "", "bucket", "count")


# -- CB5: Agent table ---------------------------------------------------------

@callback(
    Output("cc-agent-table", "data"),
    Output("cc-agent-table", "columns"),
    Input("cc-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_cc_agent_table(date_range, tenant):
    svc = ContactCenterService()
    start, end = _parse_range(date_range)
    df = svc.get_conversations_by_agent(tenant_filter=tenant, start_date=start, end_date=end)

    if df.empty:
        return [], []

    col_map = {
        "agent_id": "Agente",
        "conversations": "Conversaciones",
        "contacts": "Contactos",
    }
    columns = [{"name": col_map.get(c, c), "id": c} for c in df.columns if c in col_map]
    return df.to_dict("records"), columns


# -- CB6: Close reasons chart -------------------------------------------------

@callback(
    Output("cc-close-reasons-chart", "figure"),
    Input("cc-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_cc_close_reasons(date_range, tenant):
    svc = ContactCenterService()
    charts = ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_close_reasons(tenant_filter=tenant, start_date=start, end_date=end)
    if df.empty:
        return charts._create_empty_chart("Razones de Cierre")
    return charts._create_horizontal_bar_chart(df, "", "reason", "count")


# -- CB7: Hourly queue -------------------------------------------------------

@callback(
    Output("cc-hourly-chart", "figure"),
    Input("cc-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_cc_hourly(date_range, tenant):
    svc = ContactCenterService()
    charts = ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_hourly_queue(tenant_filter=tenant, start_date=start, end_date=end)
    if df.empty:
        return charts._create_empty_chart("Conversaciones por Hora")
    return charts.create_hourly_distribution_chart(df)
