"""Bot Performance dashboard callbacks — KPIs, fallback trend, intents, content types."""

from datetime import date, timedelta

from dash import Input, Output, callback, ctx, html
import dash_bootstrap_components as dbc

from app.services.data_service import DataService
from app.services.chart_service import ChartService


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
        md=4, sm=6, xs=12,
    )


# -- CB1: Date range selector -----------------------------------------------

@callback(
    Output("bot-date-store", "data"),
    Output("bot-date-picker", "style"),
    Output("bot-btn-7d", "active"),
    Output("bot-btn-30d", "active"),
    Output("bot-btn-90d", "active"),
    Output("bot-btn-custom", "active"),
    Input("bot-btn-7d", "n_clicks"),
    Input("bot-btn-30d", "n_clicks"),
    Input("bot-btn-90d", "n_clicks"),
    Input("bot-btn-custom", "n_clicks"),
    Input("bot-date-picker", "start_date"),
    Input("bot-date-picker", "end_date"),
)
def update_bot_date_range(_n7, _n30, _n90, _ncustom, picker_start, picker_end):
    triggered = ctx.triggered_id
    today = date.today()
    hide = {"display": "none"}
    show = {"display": "inline-block", "marginLeft": "12px"}

    if triggered == "bot-btn-7d":
        s = today - timedelta(days=6)
        return {"start": str(s), "end": str(today)}, hide, True, False, False, False
    if triggered == "bot-btn-90d":
        s = today - timedelta(days=89)
        return {"start": str(s), "end": str(today)}, hide, False, False, True, False
    if triggered == "bot-btn-custom":
        s = today - timedelta(days=29)
        return {"start": str(s), "end": str(today)}, show, False, False, False, True
    if triggered == "bot-date-picker" and picker_start and picker_end:
        return (
            {"start": str(picker_start)[:10], "end": str(picker_end)[:10]},
            show, False, False, False, True,
        )
    s = today - timedelta(days=29)
    return {"start": str(s), "end": str(today)}, hide, False, True, False, False


# -- CB2: KPI cards ----------------------------------------------------------

@callback(
    Output("bot-kpi-row", "children"),
    Input("bot-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_bot_kpis(date_range, tenant):
    svc = DataService()
    start, end = _parse_range(date_range)
    stats = svc.get_summary_stats_for_period(
        tenant_filter=tenant, start_date=start, end_date=end,
    )
    resolution = svc.get_bot_resolution_summary(
        tenant_filter=tenant, start_date=start, end_date=end,
    )
    bot_msgs = 0
    human_msgs = 0
    if not resolution.empty:
        bot_row = resolution[resolution["category"] == "Bot"]
        human_row = resolution[resolution["category"] == "Agente"]
        bot_msgs = int(bot_row["count"].iloc[0]) if not bot_row.empty else 0
        human_msgs = int(human_row["count"].iloc[0]) if not human_row.empty else 0

    return [
        _kpi_card(
            "Tasa Fallback", f"{stats['fallback_rate']}%",
            "bi-exclamation-triangle", "warning",
        ),
        _kpi_card("Mensajes Bot", bot_msgs, "bi-robot", "primary"),
        _kpi_card("Mensajes Agente", human_msgs, "bi-person", "success"),
    ]


# -- CB3: Bot vs Human chart -------------------------------------------------

@callback(
    Output("bot-vs-human-chart", "figure"),
    Input("bot-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_bot_vs_human(date_range, tenant):
    svc = DataService()
    charts = ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_bot_resolution_summary(
        tenant_filter=tenant, start_date=start, end_date=end,
    )
    if df.empty:
        return charts._create_empty_chart("Bot vs Agente")
    return charts.create_pie_chart(df, "", "category", "count")


# -- CB4: Fallback trend -----------------------------------------------------

@callback(
    Output("bot-fallback-trend-chart", "figure"),
    Input("bot-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_bot_fallback_trend(date_range, tenant):
    svc = DataService()
    charts = ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_fallback_trend_filtered(
        tenant_filter=tenant, start_date=start, end_date=end,
    )
    if df.empty or "fallback_rate" not in df.columns:
        return charts._create_empty_chart("Tendencia Fallback")
    return charts.create_chart(df, "line", "", "date", "fallback_rate")


# -- CB5: Top intents chart --------------------------------------------------

@callback(
    Output("bot-intents-chart", "figure"),
    Input("bot-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_bot_intents(date_range, tenant):
    svc = DataService()
    charts = ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_top_intents_filtered(
        tenant_filter=tenant, start_date=start, end_date=end, limit=10,
    )
    return charts.create_intent_chart(df)


# -- CB6: Content types chart ------------------------------------------------

@callback(
    Output("bot-content-chart", "figure"),
    Input("bot-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_bot_content_types(date_range, tenant):
    svc = DataService()
    charts = ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_content_type_breakdown(
        tenant_filter=tenant, start_date=start, end_date=end,
    )
    if df.empty:
        return charts._create_empty_chart("Tipos de Contenido")
    return charts.create_pie_chart(df, "", "content_type", "count")
