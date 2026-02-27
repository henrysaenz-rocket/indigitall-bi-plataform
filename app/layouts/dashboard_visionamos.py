"""Dashboard Visionamos — Analytics dashboard with date filtering and KPI storytelling."""

import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc

dash.register_page(
    __name__,
    path="/tableros/visionamos",
    name="Dashboard Visionamos",
    order=31,
)

layout = dbc.Container([
    html.H2("Dashboard Visionamos", className="page-title"),
    html.P(
        "Analitica de WhatsApp — Red Coopcentral / VirtualCoop",
        className="page-subtitle",
    ),

    # --- Date selector row ---
    dbc.Row([
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button("7D", id="dash-btn-7d", outline=True,
                           color="primary", size="sm"),
                dbc.Button("30D", id="dash-btn-30d", outline=True,
                           color="primary", size="sm", active=True),
                dbc.Button("90D", id="dash-btn-90d", outline=True,
                           color="primary", size="sm"),
                dbc.Button("Custom", id="dash-btn-custom", outline=True,
                           color="primary", size="sm"),
            ]),
            dcc.DatePickerRange(
                id="dash-date-picker",
                display_format="YYYY-MM-DD",
                style={"display": "none"},
                className="ms-3",
            ),
        ], className="d-flex align-items-center"),
    ], className="mb-4"),

    dcc.Store(id="dash-date-store", storage_type="session"),

    # --- Section 1: KPI Cards ---
    html.Div("RESUMEN EJECUTIVO", className="section-label mb-2"),
    dbc.Row(id="dash-kpi-row", className="mb-4 g-3"),

    # --- Section 2: Volume Trend + Direction ---
    html.Div("TENDENCIA DE VOLUMEN", className="section-label mb-2"),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Mensajes por Dia"),
                dbc.CardBody(
                    dcc.Loading(dcc.Graph(
                        id="dash-messages-trend-chart",
                        config={"displayModeBar": False},
                    )),
                ),
            ], className="chart-widget"),
            md=8,
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Tipo de Mensaje"),
                dbc.CardBody(
                    dcc.Loading(dcc.Graph(
                        id="dash-direction-chart",
                        config={"displayModeBar": False},
                    )),
                ),
            ], className="chart-widget"),
            md=4,
        ),
    ], className="mb-4 g-3"),

    # --- Section 3: Behavioral Patterns ---
    html.Div("PATRONES DE COMPORTAMIENTO", className="section-label mb-2"),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Distribucion Horaria"),
                dbc.CardBody(
                    dcc.Loading(dcc.Graph(
                        id="dash-hourly-chart",
                        config={"displayModeBar": False},
                    )),
                ),
            ], className="chart-widget"),
            md=6,
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Actividad por Dia de Semana"),
                dbc.CardBody(
                    dcc.Loading(dcc.Graph(
                        id="dash-dow-chart",
                        config={"displayModeBar": False},
                    )),
                ),
            ], className="chart-widget"),
            md=6,
        ),
    ], className="mb-4 g-3"),

    # --- Section 4: Intents + Bot vs Human ---
    html.Div("INTENCIONES Y AUTOMATIZACION", className="section-label mb-2"),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Top Intenciones"),
                dbc.CardBody(
                    dcc.Loading(dcc.Graph(
                        id="dash-intents-chart",
                        config={"displayModeBar": False},
                    )),
                ),
            ], className="chart-widget"),
            md=7,
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Bot vs Agente vs Usuario"),
                dbc.CardBody(
                    dcc.Loading(dcc.Graph(
                        id="dash-bot-human-chart",
                        config={"displayModeBar": False},
                    )),
                ),
            ], className="chart-widget"),
            md=5,
        ),
    ], className="mb-4 g-3"),

    # --- Section 5: Agent Performance ---
    html.Div("RENDIMIENTO DE AGENTES", className="section-label mb-2"),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Tabla de Agentes"),
                dbc.CardBody(
                    dcc.Loading(
                        dash_table.DataTable(
                            id="dash-agent-table",
                            sort_action="native",
                            page_size=10,
                            style_table={"overflowX": "auto"},
                            style_cell={
                                "textAlign": "left",
                                "padding": "8px",
                                "fontFamily": "Inter, sans-serif",
                                "fontSize": "13px",
                            },
                            style_header={
                                "backgroundColor": "#F5F7FA",
                                "fontWeight": "600",
                                "border": "1px solid #E4E4E7",
                            },
                            style_data={"border": "1px solid #E4E4E7"},
                            style_data_conditional=[
                                {"if": {"row_index": "odd"},
                                 "backgroundColor": "#FAFBFC"},
                            ],
                        ),
                    ),
                ),
            ], className="chart-widget"),
            md=12,
        ),
    ], className="mb-4"),
], fluid=True, className="py-4")
