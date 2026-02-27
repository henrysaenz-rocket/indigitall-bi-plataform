"""Bot Performance Dashboard — Fallback rate, bot vs human, intent analysis."""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(
    __name__,
    path="/tableros/bot-performance",
    name="Bot / Automatizacion",
    order=33,
)

layout = dbc.Container([
    html.H2("Bot / Automatizacion", className="page-title"),
    html.P(
        "Rendimiento del chatbot, tasa de fallback y distribucion de intenciones",
        className="page-subtitle",
    ),

    # --- Date selector row ---
    dbc.Row([
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button("7D", id="bot-btn-7d", outline=True, color="primary", size="sm"),
                dbc.Button("30D", id="bot-btn-30d", outline=True, color="primary", size="sm", active=True),
                dbc.Button("90D", id="bot-btn-90d", outline=True, color="primary", size="sm"),
                dbc.Button("Custom", id="bot-btn-custom", outline=True, color="primary", size="sm"),
            ]),
            dcc.DatePickerRange(
                id="bot-date-picker",
                display_format="YYYY-MM-DD",
                style={"display": "none"},
                className="ms-3",
            ),
        ], className="d-flex align-items-center"),
    ], className="mb-4"),

    dcc.Store(id="bot-date-store", storage_type="session"),

    # --- KPI Cards ---
    html.Div("RESUMEN BOT", className="section-label mb-2"),
    dbc.Row(id="bot-kpi-row", className="mb-4 g-3"),

    # --- Bot vs Human + Fallback trend ---
    html.Div("AUTOMATIZACION VS HUMANO", className="section-label mb-2"),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Bot vs Agente"),
                dbc.CardBody(dcc.Loading(dcc.Graph(
                    id="bot-vs-human-chart", config={"displayModeBar": False},
                ))),
            ], className="chart-widget"),
            md=4,
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Tendencia de Fallback"),
                dbc.CardBody(dcc.Loading(dcc.Graph(
                    id="bot-fallback-trend-chart", config={"displayModeBar": False},
                ))),
            ], className="chart-widget"),
            md=8,
        ),
    ], className="mb-4 g-3"),

    # --- Intents + Content types ---
    html.Div("INTENCIONES Y CONTENIDO", className="section-label mb-2"),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Top Intenciones"),
                dbc.CardBody(dcc.Loading(dcc.Graph(
                    id="bot-intents-chart", config={"displayModeBar": False},
                ))),
            ], className="chart-widget"),
            md=7,
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Tipos de Contenido"),
                dbc.CardBody(dcc.Loading(dcc.Graph(
                    id="bot-content-chart", config={"displayModeBar": False},
                ))),
            ], className="chart-widget"),
            md=5,
        ),
    ], className="mb-4 g-3"),
], fluid=True, className="py-4")
