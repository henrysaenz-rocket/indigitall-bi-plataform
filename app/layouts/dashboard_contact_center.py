"""Contact Center Dashboard — Conversation analytics, agent performance, wait times."""

import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc

dash.register_page(
    __name__,
    path="/tableros/contact-center",
    name="Contact Center",
    order=32,
)

layout = dbc.Container([
    html.H2("Contact Center", className="page-title"),
    html.P(
        "Conversaciones de agentes, tiempos de espera y razon de cierre",
        className="page-subtitle",
    ),

    # --- Date selector row ---
    dbc.Row([
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button("7D", id="cc-btn-7d", outline=True, color="primary", size="sm"),
                dbc.Button("30D", id="cc-btn-30d", outline=True, color="primary", size="sm", active=True),
                dbc.Button("90D", id="cc-btn-90d", outline=True, color="primary", size="sm"),
                dbc.Button("Custom", id="cc-btn-custom", outline=True, color="primary", size="sm"),
            ]),
            dcc.DatePickerRange(
                id="cc-date-picker",
                display_format="YYYY-MM-DD",
                style={"display": "none"},
                className="ms-3",
            ),
        ], className="d-flex align-items-center"),
    ], className="mb-4"),

    dcc.Store(id="cc-date-store", storage_type="session"),

    # --- KPI Cards ---
    html.Div("RESUMEN CONTACT CENTER", className="section-label mb-2"),
    dbc.Row(id="cc-kpi-row", className="mb-4 g-3"),

    # --- Conversations over time ---
    html.Div("VOLUMEN DE CONVERSACIONES", className="section-label mb-2"),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Conversaciones por Dia"),
                dbc.CardBody(dcc.Loading(dcc.Graph(
                    id="cc-conv-trend-chart", config={"displayModeBar": False},
                ))),
            ], className="chart-widget"),
            md=8,
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Distribucion de Espera"),
                dbc.CardBody(dcc.Loading(dcc.Graph(
                    id="cc-wait-distribution-chart", config={"displayModeBar": False},
                ))),
            ], className="chart-widget"),
            md=4,
        ),
    ], className="mb-4 g-3"),

    # --- Agent table + Close reasons ---
    html.Div("AGENTES Y RAZONES DE CIERRE", className="section-label mb-2"),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Top Agentes"),
                dbc.CardBody(dcc.Loading(
                    dash_table.DataTable(
                        id="cc-agent-table",
                        sort_action="native",
                        page_size=10,
                        style_table={"overflowX": "auto"},
                        style_cell={
                            "textAlign": "left", "padding": "8px",
                            "fontFamily": "Inter, sans-serif", "fontSize": "13px",
                        },
                        style_header={
                            "backgroundColor": "#F5F7FA", "fontWeight": "600",
                            "border": "1px solid #E4E4E7",
                        },
                        style_data={"border": "1px solid #E4E4E7"},
                        style_data_conditional=[
                            {"if": {"row_index": "odd"}, "backgroundColor": "#FAFBFC"},
                        ],
                    ),
                )),
            ], className="chart-widget"),
            md=7,
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Razones de Cierre"),
                dbc.CardBody(dcc.Loading(dcc.Graph(
                    id="cc-close-reasons-chart", config={"displayModeBar": False},
                ))),
            ], className="chart-widget"),
            md=5,
        ),
    ], className="mb-4 g-3"),

    # --- Hourly queue ---
    html.Div("DISTRIBUCION HORARIA", className="section-label mb-2"),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Conversaciones por Hora"),
                dbc.CardBody(dcc.Loading(dcc.Graph(
                    id="cc-hourly-chart", config={"displayModeBar": False},
                ))),
            ], className="chart-widget"),
            md=12,
        ),
    ], className="mb-4"),
], fluid=True, className="py-4")
