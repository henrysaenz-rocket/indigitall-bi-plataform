"""Control de Toques dashboard callbacks — KPIs, distribution, trend, export."""

from datetime import date, timedelta

import pandas as pd
from dash import Input, Output, State, callback, ctx, html, dcc
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

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
        md=3, sm=6, xs=12,
    )


# -- CB1: Date range selector -----------------------------------------------

@callback(
    Output("tq-date-store", "data"),
    Output("tq-date-picker", "style"),
    Output("tq-btn-7d", "active"),
    Output("tq-btn-30d", "active"),
    Output("tq-btn-90d", "active"),
    Output("tq-btn-custom", "active"),
    Input("tq-btn-7d", "n_clicks"),
    Input("tq-btn-30d", "n_clicks"),
    Input("tq-btn-90d", "n_clicks"),
    Input("tq-btn-custom", "n_clicks"),
    Input("tq-date-picker", "start_date"),
    Input("tq-date-picker", "end_date"),
)
def update_tq_date_range(_n7, _n30, _n90, _ncustom, picker_start, picker_end):
    triggered = ctx.triggered_id
    today = date.today()
    hide = {"display": "none"}
    show = {"display": "inline-block", "marginLeft": "12px"}

    if triggered == "tq-btn-7d":
        s = today - timedelta(days=6)
        return {"start": str(s), "end": str(today)}, hide, True, False, False, False
    if triggered == "tq-btn-90d":
        s = today - timedelta(days=89)
        return {"start": str(s), "end": str(today)}, hide, False, False, True, False
    if triggered == "tq-btn-custom":
        s = today - timedelta(days=29)
        return {"start": str(s), "end": str(today)}, show, False, False, False, True
    if triggered == "tq-date-picker" and picker_start and picker_end:
        return (
            {"start": str(picker_start)[:10], "end": str(picker_end)[:10]},
            show, False, False, False, True,
        )
    s = today - timedelta(days=29)
    return {"start": str(s), "end": str(today)}, hide, False, True, False, False


# -- CB2: KPI cards ----------------------------------------------------------

@callback(
    Output("tq-kpi-row", "children"),
    Input("tq-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_tq_kpis(date_range, tenant):
    svc = DataService()
    start, end = _parse_range(date_range)
    kpis = svc.get_toques_kpis(tenant_filter=tenant, start_date=start, end_date=end)
    return [
        _kpi_card(
            "% Sobre-tocados", f"{kpis['pct_over_touched']}%",
            "bi-exclamation-octagon", "danger",
        ),
        _kpi_card(
            "Sobre-tocados", kpis["over_touched"],
            "bi-bell-exclamation", "warning",
        ),
        _kpi_card(
            "Contacto/Semanas", kpis["total_contact_weeks"],
            "bi-calendar-week", "info",
        ),
        _kpi_card(
            "Prom Msgs/Sem", f"{kpis['avg_msgs_per_contact_week']}",
            "bi-graph-up", "primary",
        ),
    ]


# -- CB3: Distribution chart -------------------------------------------------

@callback(
    Output("tq-distribution-chart", "figure"),
    Input("tq-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_tq_distribution(date_range, tenant):
    svc = DataService()
    charts = ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_toques_distribution(tenant_filter=tenant, start_date=start, end_date=end)
    if df.empty:
        return charts._create_empty_chart("Distribucion de Toques")
    return charts.create_bar_chart(df, "", "bucket", "count")


# -- CB4: Weekly trend -------------------------------------------------------

@callback(
    Output("tq-trend-chart", "figure"),
    Input("tq-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_tq_trend(date_range, tenant):
    svc = DataService()
    charts = ChartService()
    start, end = _parse_range(date_range)
    df = svc.get_toques_weekly_trend(tenant_filter=tenant, start_date=start, end_date=end)
    if df.empty or "pct_over_touched" not in df.columns:
        return charts._create_empty_chart("Tendencia Semanal")
    return charts.create_chart(df, "line", "", "week", "pct_over_touched")


# -- CB5: Over-touched contacts table ----------------------------------------

@callback(
    Output("tq-contacts-table", "data"),
    Output("tq-contacts-table", "columns"),
    Input("tq-date-store", "data"),
    Input("tenant-context", "data"),
)
def load_tq_contacts(date_range, tenant):
    svc = DataService()
    start, end = _parse_range(date_range)
    df = svc.get_over_touched_contacts(tenant_filter=tenant, start_date=start, end_date=end)

    if df.empty:
        return [], []

    col_map = {
        "contact_id": "ID Contacto",
        "contact_name": "Contacto",
        "semana": "Semana",
        "mensajes": "Mensajes",
    }
    available = [c for c in col_map if c in df.columns]
    columns = [{"name": col_map[c], "id": c} for c in available]
    return df[available].to_dict("records"), columns


# -- CB6: CSV Export ----------------------------------------------------------

@callback(
    Output("tq-download-csv", "data"),
    Input("tq-export-csv-btn", "n_clicks"),
    State("tq-date-store", "data"),
    State("tenant-context", "data"),
    prevent_initial_call=True,
)
def export_tq_csv(n_clicks, date_range, tenant):
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
