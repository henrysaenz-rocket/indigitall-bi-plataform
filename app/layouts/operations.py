"""Operations dashboard — Chat analytics with date filtering."""

import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/operaciones", name="Operaciones", order=1)

layout = dbc.Container([
    html.H2("Operaciones", className="page-title"),
    html.P("Analítica operativa de chat — filtros de fecha y KPIs con tendencia.",
           className="page-subtitle"),

    # --- Date selector row ---
    dbc.Row([
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button("7D", id="ops-btn-7d", outline=True,
                           color="primary", size="sm"),
                dbc.Button("30D", id="ops-btn-30d", outline=True,
                           color="primary", size="sm", active=True),
                dbc.Button("90D", id="ops-btn-90d", outline=True,
                           color="primary", size="sm"),
                dbc.Button("Custom", id="ops-btn-custom", outline=True,
                           color="primary", size="sm"),
            ]),
            dcc.DatePickerRange(
                id="ops-date-picker",
                display_format="YYYY-MM-DD",
                style={"display": "none"},
                className="ms-3",
            ),
        ], className="d-flex align-items-center"),
    ], className="mb-4"),

    # Session store for selected range
    dcc.Store(id="ops-date-store", storage_type="session"),

    # --- KPI cards ---
    dbc.Row(id="ops-kpi-row", className="mb-4 g-3"),

    # --- Charts row ---
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Mensajes por Día"),
                dbc.CardBody(
                    dcc.Loading(dcc.Graph(
                        id="ops-messages-trend-chart",
                        config={"displayModeBar": False},
                    )),
                ),
            ], className="chart-widget"),
            md=8,
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Distribución por Dirección"),
                dbc.CardBody(
                    dcc.Loading(dcc.Graph(
                        id="ops-direction-chart",
                        config={"displayModeBar": False},
                    )),
                ),
            ], className="chart-widget"),
            md=4,
        ),
    ], className="mb-4 g-3"),

    # --- Agent performance table ---
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Rendimiento de Agentes"),
                dbc.CardBody(
                    dcc.Loading(
                        dash_table.DataTable(
                            id="ops-agent-table",
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
