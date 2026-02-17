"""Dashboard view callbacks — load dashboard, render widgets, toggle AI chat."""

import json

import pandas as pd
from dash import (
    Input, Output, State, callback, html, dcc, no_update, ctx,
)
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import plotly.express as px

from app.services.storage_service import StorageService
from app.config import settings

CHART_COLORS = ["#1E88E5", "#76C043", "#A0A3BD", "#42A5F5", "#1565C0", "#FFC107", "#9C27B0", "#FF5722"]


def _render_widget(widget):
    """Render a single dashboard widget card from its config."""
    widget_type = widget.get("type", "table")
    title = widget.get("title", "Widget")
    query_id = widget.get("query_id")
    data = widget.get("data", [])
    columns = widget.get("columns", [])

    body_content = []

    if not data:
        body_content.append(
            html.Div([
                html.I(className="bi bi-inbox text-muted"),
                html.Small(" Sin datos", className="text-muted"),
            ], className="text-center py-3")
        )
    else:
        df = pd.DataFrame(data)

        # Chart
        if widget_type in ("bar", "line", "pie") and len(df.columns) >= 2:
            x_col, y_col = df.columns[0], df.columns[1]
            if widget_type == "line":
                fig = px.line(df, x=x_col, y=y_col, color_discrete_sequence=CHART_COLORS)
            elif widget_type == "pie":
                fig = px.pie(df, names=x_col, values=y_col, color_discrete_sequence=CHART_COLORS)
            else:
                fig = px.bar(df, x=x_col, y=y_col, color_discrete_sequence=CHART_COLORS)

            fig.update_layout(
                template="plotly_white",
                font_family="Inter, sans-serif",
                margin=dict(l=10, r=10, t=10, b=10),
                height=250,
                showlegend=False,
            )
            body_content.append(dcc.Graph(figure=fig, config={"displayModeBar": False}))

        # Table
        if widget_type == "table" or widget.get("show_table"):
            from dash import dash_table
            body_content.append(
                dash_table.DataTable(
                    data=data[:50],
                    columns=[{"name": c, "id": c} for c in columns],
                    page_size=10,
                    style_table={"overflowX": "auto"},
                    style_header={
                        "backgroundColor": "#F5F7FA",
                        "fontWeight": "600",
                        "fontSize": "12px",
                        "color": "#6E7191",
                    },
                    style_cell={
                        "fontSize": "12px",
                        "fontFamily": "Inter, sans-serif",
                        "padding": "6px 8px",
                    },
                )
            )

    return dbc.Col(
        dbc.Card([
            dbc.CardHeader([
                html.Span(title, className="fw-semibold small"),
            ], className="py-2 px-3 bg-white"),
            dbc.CardBody(body_content, className="p-2"),
        ], className="dashboard-widget h-100"),
        md=widget.get("width", 6),
        className="mb-3",
    )


# --- Load dashboard ---

@callback(
    Output("dashboard-grid", "children"),
    Input("url", "pathname"),
    State("tenant-context", "data"),
)
def load_dashboard(pathname, tenant):
    if not pathname or not pathname.startswith("/tableros/"):
        raise PreventUpdate

    # Extract dashboard_id from path
    parts = pathname.strip("/").split("/")
    if len(parts) < 2 or parts[1] in ("nuevo", ""):
        raise PreventUpdate

    dashboard_id = parts[1]

    svc = StorageService(tenant_id=tenant or settings.DEFAULT_TENANT)
    result = svc.get_dashboard(dashboard_id)

    if not result:
        return html.Div([
            html.I(className="bi bi-exclamation-triangle display-4 text-warning"),
            html.P("Tablero no encontrado.", className="text-muted mt-3"),
            dbc.Button("Volver a tableros", href="/tableros", color="primary", size="sm"),
        ], className="text-center py-5")

    layout = result.get("layout") or []
    if not layout:
        return html.Div([
            html.I(className="bi bi-grid-1x2 display-4 text-muted"),
            html.P("Este tablero no tiene widgets. Agrega consultas guardadas como widgets.",
                   className="text-muted mt-3"),
        ], className="text-center py-5")

    widgets = [_render_widget(w) for w in layout]
    return dbc.Row(widgets, className="g-3")


# --- Toggle AI chat offcanvas ---

@callback(
    Output("ai-chat-offcanvas", "is_open"),
    Input("open-ai-chat", "n_clicks"),
    State("ai-chat-offcanvas", "is_open"),
    prevent_initial_call=True,
)
def toggle_ai_chat(n_clicks, is_open):
    return not is_open
