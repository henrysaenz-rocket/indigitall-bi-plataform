"""Operations dashboard callbacks — date range, KPIs, charts, agent table."""

from datetime import date, timedelta

from dash import Input, Output, callback, ctx, html
import dash_bootstrap_components as dbc

from app.services.data_service import DataService
from app.services.chart_service import ChartService


# ── Helpers ──────────────────────────────────────────────────────────

def _calc_trend(current, previous):
    """Percentage change; returns None when comparison is impossible."""
    if previous == 0:
        return None
    return round((current - previous) / previous * 100, 1)


def _ops_kpi_card(label, value, icon, trend_pct=None):
    """Single KPI card with optional green/red trend badge."""
    trend_badge = []
    if trend_pct is not None and trend_pct != 0:
        color = "success" if trend_pct > 0 else "danger"
        arrow = "\u2191" if trend_pct > 0 else "\u2193"
        trend_badge = [
            dbc.Badge(
                f"{arrow} {abs(trend_pct):.1f}%",
                color=color,
                className="ms-2",
            ),
        ]

    display_value = f"{value:,}" if isinstance(value, int) else str(value)

    return dbc.Col(
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className=f"bi {icon} me-2 text-primary"),
                    html.Span(label, className="kpi-label"),
                ]),
                html.Div([
                    html.Span(display_value, className="kpi-value"),
                    *trend_badge,
                ], className="d-flex align-items-center mt-1"),
            ]),
        ], className="kpi-card"),
        md=True, sm=6, xs=12,
    )


def _parse_range(date_range):
    """Extract (start, end) date objects from the store dict."""
    if date_range:
        return (
            date.fromisoformat(str(date_range["start"])[:10]),
            date.fromisoformat(str(date_range["end"])[:10]),
        )
    today = date.today()
    return today - timedelta(days=29), today


# ── CB1: Date range selector ────────────────────────────────────────

@callback(
    Output("ops-date-store", "data"),
    Output("ops-date-picker", "style"),
    Output("ops-btn-7d", "active"),
    Output("ops-btn-30d", "active"),
    Output("ops-btn-90d", "active"),
    Output("ops-btn-custom", "active"),
    Input("ops-btn-7d", "n_clicks"),
    Input("ops-btn-30d", "n_clicks"),
    Input("ops-btn-90d", "n_clicks"),
    Input("ops-btn-custom", "n_clicks"),
    Input("ops-date-picker", "start_date"),
    Input("ops-date-picker", "end_date"),
)
def update_date_range(_n7, _n30, _n90, _ncustom, picker_start, picker_end):
    triggered = ctx.triggered_id
    today = date.today()
    hide = {"display": "none"}
    show = {"display": "inline-block", "marginLeft": "12px"}

    if triggered == "ops-btn-7d":
        s = today - timedelta(days=6)
        return {"start": str(s), "end": str(today)}, hide, True, False, False, False

    if triggered == "ops-btn-90d":
        s = today - timedelta(days=89)
        return {"start": str(s), "end": str(today)}, hide, False, False, True, False

    if triggered == "ops-btn-custom":
        s = today - timedelta(days=29)
        return {"start": str(s), "end": str(today)}, show, False, False, False, True

    if triggered == "ops-date-picker" and picker_start and picker_end:
        return (
            {"start": str(picker_start)[:10], "end": str(picker_end)[:10]},
            show, False, False, False, True,
        )

    # Default: 30D
    s = today - timedelta(days=29)
    return {"start": str(s), "end": str(today)}, hide, False, True, False, False


# ── CB2: KPI cards with trend badges ────────────────────────────────

@callback(
    Output("ops-kpi-row", "children"),
    Input("ops-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_ops_kpis(date_range, tenant):
    svc = DataService()
    start, end = _parse_range(date_range)
    stats = svc.get_summary_stats_for_period(
        tenant_filter=tenant, start_date=start, end_date=end,
    )

    return [
        _ops_kpi_card(
            "Total Mensajes", stats["total_messages"], "bi-chat-left-text",
            _calc_trend(stats["total_messages"], stats["prev_total_messages"]),
        ),
        _ops_kpi_card(
            "Contactos Únicos", stats["unique_contacts"], "bi-people",
            _calc_trend(stats["unique_contacts"], stats["prev_unique_contacts"]),
        ),
        _ops_kpi_card(
            "Conversaciones", stats["conversations"], "bi-chat-square-dots",
            _calc_trend(stats["conversations"], stats["prev_conversations"]),
        ),
        _ops_kpi_card(
            "T.Espera Prom", f"{stats['avg_wait_seconds']}s", "bi-clock",
            _calc_trend(stats["avg_wait_seconds"], stats["prev_avg_wait_seconds"]),
        ),
        _ops_kpi_card(
            "Fallback Rate", f"{stats['fallback_rate']}%", "bi-exclamation-triangle",
            _calc_trend(stats["fallback_rate"], stats["prev_fallback_rate"]),
        ),
    ]


# ── CB3: Messages-over-time line chart ──────────────────────────────

@callback(
    Output("ops-messages-trend-chart", "figure"),
    Input("ops-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_messages_trend(date_range, tenant):
    svc = DataService()
    charts = ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_messages_over_time_filtered(
        tenant_filter=tenant, start_date=start, end_date=end,
    )
    return charts.create_messages_over_time_chart(df)


# ── CB4: Direction donut chart ──────────────────────────────────────

@callback(
    Output("ops-direction-chart", "figure"),
    Input("ops-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_direction_chart(date_range, tenant):
    svc = DataService()
    charts = ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_direction_breakdown_filtered(
        tenant_filter=tenant, start_date=start, end_date=end,
    )
    return charts.create_messages_by_direction_chart(df)


# ── CB5: Agent performance DataTable ────────────────────────────────

@callback(
    Output("ops-agent-table", "data"),
    Output("ops-agent-table", "columns"),
    Input("tenant-context", "data"),
)
def load_agent_table(tenant):
    svc = DataService()
    df = svc.get_agent_performance_detailed(tenant_filter=tenant)

    if df.empty:
        return [], []

    col_map = {
        "agent_id": "Agente",
        "total_messages": "Mensajes",
        "conversations_handled": "Conversaciones",
        "unique_contacts": "Contactos",
        "avg_handle_seconds": "T.Manejo(s)",
        "avg_wait_seconds": "T.Espera(s)",
        "active_days": "Días Activos",
    }

    available = [c for c in col_map if c in df.columns]
    df = df[available].copy()

    for col in ("avg_handle_seconds", "avg_wait_seconds"):
        if col in df.columns:
            df[col] = df[col].round(1)

    columns = [{"name": col_map[c], "id": c} for c in available]
    return df.to_dict("records"), columns
