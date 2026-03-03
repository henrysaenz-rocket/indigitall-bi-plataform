"""Unified Dashboard — SMS tab callbacks (all from sms_envios).

Available data: total_enviados, total_chunks, campanas, tipos_envio,
sends_vs_chunks trend, heatmap, campaign ranking, type breakdown,
detail table, drill-down.
"""

import logging
import calendar
from datetime import date, timedelta

from dash import Input, Output, State, callback, ctx, dcc, html
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

from app.callbacks.ud_shared import parse_range, kpi_card, no_data_alert, empty_figure
from app.services.sms_data_service import SmsDataService
from app.services.chart_service import ChartService

log = logging.getLogger(__name__)


def _month_to_range(month_str):
    """Convert 'YYYY-MM' to (start_date, end_date)."""
    year, month = map(int, month_str.split("-"))
    start = date(year, month, 1)
    _, last_day = calendar.monthrange(year, month)
    return start, date(year, month, last_day)


def _week_to_range(week_str):
    """Convert 'YYYY-WNN' to (start_date, end_date)."""
    parts = week_str.split("-W")
    if len(parts) == 2:
        year, week = int(parts[0]), int(parts[1])
    else:
        p = week_str.replace("W", "").split("-")
        year, week = int(p[0]), int(p[-1])
    start = date.fromisocalendar(year, week, 1)
    return start, start + timedelta(days=6)


# ==================== KPIs ====================

@callback(
    Output("ud-sms-kpi-row", "children"),
    Input("ud-date-store", "data"),
)
def load_ud_sms_kpis(date_range):
    try:
        svc = SmsDataService()
        start, end = parse_range(date_range)
        kpis = svc.get_sms_kpis(start_date=start, end_date=end)
        has_data = kpis["total_enviados"] > 0
    except Exception:
        log.exception("Error loading SMS KPIs")
        kpis = {"total_enviados": 0, "total_chunks": 0, "campanas": 0, "tipos_envio": 0}
        has_data = False

    cards = [
        kpi_card("Enviados", kpis["total_enviados"], "bi-send", md=3),
        kpi_card("Chunks", kpis["total_chunks"], "bi-stack", md=3),
        kpi_card("Campanas", kpis["campanas"], "bi-megaphone", "info", md=3),
        kpi_card("Tipos Envio", kpis["tipos_envio"], "bi-diagram-3", "primary", md=3),
    ]
    if not has_data:
        return [dbc.Col(no_data_alert("SMS"), md=12)] + cards
    return cards


# ==================== Sends vs Chunks Trend ====================

@callback(
    Output("ud-sms-sends-chunks-chart", "figure"),
    Input("ud-date-store", "data"),
)
def load_ud_sms_sends_chunks(date_range):
    try:
        svc, charts = SmsDataService(), ChartService()
        start, end = parse_range(date_range)
        df = svc.get_sends_vs_chunks_trend(start_date=start, end_date=end)
        if df.empty or df["enviados"].sum() == 0:
            return empty_figure("Enviados vs Chunks")
        return charts.create_multi_line_chart(
            df, "", "date", ["enviados", "chunks"],
            {"enviados": "Enviados", "chunks": "Chunks"},
        )
    except Exception:
        log.exception("Error loading SMS sends vs chunks")
        return empty_figure("Enviados vs Chunks")


# ==================== Heatmap ====================

@callback(
    Output("ud-sms-heatmap-chart", "figure"),
    Input("ud-date-store", "data"),
)
def load_ud_sms_heatmap(date_range):
    try:
        svc, charts = SmsDataService(), ChartService()
        start, end = parse_range(date_range)
        df = svc.get_heatmap_data(start_date=start, end_date=end)
        if df.empty:
            return empty_figure("Mapa de Calor SMS")
        return charts.create_heatmap(df, "", "hora", "dia_semana", "value")
    except Exception:
        log.exception("Error loading SMS heatmap")
        return empty_figure("Mapa de Calor SMS")


# ==================== Rankings ====================

@callback(
    Output("ud-sms-ranking-chart", "figure"),
    Input("ud-date-store", "data"),
)
def load_ud_sms_ranking(date_range):
    try:
        svc, charts = SmsDataService(), ChartService()
        start, end = parse_range(date_range)
        df = svc.get_campaign_ranking(start_date=start, end_date=end, limit=10)
        if df.empty:
            return empty_figure("Sin datos de campanas")
        return charts.create_ranking_bar_chart(
            df, "", "campana_nombre", "total_enviados",
        )
    except Exception:
        log.exception("Error loading SMS ranking")
        return empty_figure("Sin datos de campanas")


@callback(
    Output("ud-sms-ranking-ctr-chart", "figure"),
    Input("ud-date-store", "data"),
)
def load_ud_sms_ranking_ctr(date_range):
    try:
        svc, charts = SmsDataService(), ChartService()
        start, end = parse_range(date_range)
        df = svc.get_campaign_ranking_by_ctr(start_date=start, end_date=end, limit=10)
        if df.empty:
            return empty_figure("Sin campanas con >100 envios")
        return charts.create_ranking_bar_chart(
            df, "", "campana_nombre", "chunks_per_send",
        )
    except Exception:
        log.exception("Error loading SMS ranking by efficiency")
        return empty_figure("Sin datos de campanas")


# ==================== Type Breakdown ====================

@callback(
    Output("ud-sms-type-chart", "figure"),
    Input("ud-date-store", "data"),
)
def load_ud_sms_type(date_range):
    try:
        svc, charts = SmsDataService(), ChartService()
        start, end = parse_range(date_range)
        df = svc.get_sending_type_breakdown(start_date=start, end_date=end)
        if df.empty:
            return empty_figure("Tipo de Envio")
        return charts.create_bar_chart(df, "", "sending_type", "count")
    except Exception:
        log.exception("Error loading SMS type")
        return empty_figure("Tipo de Envio")


# ==================== Detail Table ====================

@callback(
    Output("ud-sms-detail-table", "data"),
    Output("ud-sms-detail-table", "columns"),
    Output("ud-sms-detail-total", "children"),
    Input("ud-date-store", "data"),
)
def load_ud_sms_detail_table(date_range):
    try:
        svc = SmsDataService()
        start, end = parse_range(date_range)
        df, total = svc.get_detail_page(
            start_date=start, end_date=end, page=0, page_size=200,
        )
        if df.empty:
            return [], [], "0 registros"
        col_map = {
            "fecha": "Fecha",
            "campaign_id": "Campana ID",
            "sending_type": "Tipo de Envio",
            "total_chunks": "Chunks",
            "is_flash": "Flash",
        }
        columns = [
            {"name": col_map.get(c, c), "id": c}
            for c in df.columns if c in col_map
        ]
        return df.to_dict("records"), columns, f"{total:,} registros"
    except Exception:
        log.exception("Error loading SMS detail table")
        return [], [], "Error"


@callback(
    Output("ud-sms-download-csv", "data"),
    Input("ud-sms-export-csv-btn", "n_clicks"),
    State("ud-date-store", "data"),
    prevent_initial_call=True,
)
def export_ud_sms_csv(n_clicks, date_range):
    if not n_clicks:
        raise PreventUpdate
    svc = SmsDataService()
    start, end = parse_range(date_range)
    df, _ = svc.get_detail_page(
        start_date=start, end_date=end, page=0, page_size=5000,
    )
    if df.empty:
        raise PreventUpdate
    return dcc.send_data_frame(df.to_csv, "sms_detalle.csv", index=False)


# ==================== Drill-Down (3-level interactive) ====================

@callback(
    Output("ud-sms-drill-store", "data"),
    Input("ud-sms-drill-graph", "clickData"),
    Input("ud-sms-drill-reset", "n_clicks"),
    State("ud-sms-drill-store", "data"),
    prevent_initial_call=True,
)
def navigate_sms_drill(click_data, reset_clicks, state):
    """Handle drill-down: click bar to drill deeper, reset to go back."""
    trigger = ctx.triggered_id
    if trigger == "ud-sms-drill-reset":
        return {"level": "month", "month": None, "week": None}

    if not click_data:
        raise PreventUpdate

    level = (state or {}).get("level", "month")
    clicked = str(click_data["points"][0]["x"])

    if level == "month":
        return {"level": "week", "month": clicked, "week": None}
    elif level == "week":
        return {"level": "day", "month": state.get("month"), "week": clicked}
    raise PreventUpdate


@callback(
    Output("ud-sms-drill-breadcrumb", "children"),
    Output("ud-sms-drill-graph", "figure"),
    Output("ud-sms-drill-reset", "style"),
    Input("ud-sms-drill-store", "data"),
    Input("ud-date-store", "data"),
)
def render_sms_drill(state, date_range):
    """Render drill chart, breadcrumb, and reset button visibility."""
    level = (state or {}).get("level", "month")
    month_f = (state or {}).get("month")
    week_f = (state or {}).get("week")

    try:
        svc, charts = SmsDataService(), ChartService()
        start, end = parse_range(date_range)

        if level == "week" and month_f:
            try:
                start, end = _month_to_range(month_f)
            except (ValueError, IndexError):
                pass
        elif level == "day" and week_f:
            try:
                start, end = _week_to_range(week_f)
            except (ValueError, IndexError):
                pass

        df = svc.get_drill_data(
            start_date=start, end_date=end, granularity=level,
        )
        if df.empty:
            fig = empty_figure("Sin datos")
        else:
            fig = charts.create_bar_chart(df, "", "period", "total")
    except Exception:
        log.exception("Error loading SMS drill")
        fig = empty_figure("Error")

    level_labels = {"month": "Meses", "week": "Semanas", "day": "Dias"}
    crumbs = [html.Span(
        f"Vista: {level_labels.get(level, level)}",
        style={"fontSize": "13px", "fontWeight": "600", "color": "#1A1A2E"},
    )]
    if month_f:
        crumbs.append(html.Span(
            f" / {month_f}",
            style={"fontSize": "13px", "color": "#6E7191"},
        ))
    if week_f:
        crumbs.append(html.Span(
            f" / {week_f}",
            style={"fontSize": "13px", "color": "#6E7191"},
        ))

    reset_style = (
        {"display": "none"} if level == "month"
        else {"borderRadius": "8px", "fontSize": "12px"}
    )
    return html.Div(crumbs), fig, reset_style
