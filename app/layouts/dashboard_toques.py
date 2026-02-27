"""Control de Toques Dashboard — Contact frequency analysis per user per week."""

import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc

dash.register_page(
    __name__,
    path="/tableros/control-toques",
    name="Control de Toques",
    order=34,
)

layout = dbc.Container([
    html.H2("Control de Toques", className="page-title"),
    html.P(
        "Frecuencia de mensajes por contacto por semana — identifica usuarios sobre-tocados",
        className="page-subtitle",
    ),

    # --- Date selector row ---
    dbc.Row([
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button("7D", id="tq-btn-7d", outline=True, color="primary", size="sm"),
                dbc.Button("30D", id="tq-btn-30d", outline=True, color="primary", size="sm", active=True),
                dbc.Button("90D", id="tq-btn-90d", outline=True, color="primary", size="sm"),
                dbc.Button("Custom", id="tq-btn-custom", outline=True, color="primary", size="sm"),
            ]),
            dcc.DatePickerRange(
                id="tq-date-picker",
                display_format="YYYY-MM-DD",
                style={"display": "none"},
                className="ms-3",
            ),
        ], className="d-flex align-items-center"),
    ], className="mb-4"),

    dcc.Store(id="tq-date-store", storage_type="session"),

    # --- Big KPI ---
    html.Div("RESUMEN DE TOQUES", className="section-label mb-2"),
    dbc.Row(id="tq-kpi-row", className="mb-4 g-3"),

    # --- Distribution histogram + Weekly trend ---
    html.Div("DISTRIBUCION Y TENDENCIA", className="section-label mb-2"),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Mensajes por Contacto/Semana"),
                dbc.CardBody(dcc.Loading(dcc.Graph(
                    id="tq-distribution-chart", config={"displayModeBar": False},
                ))),
            ], className="chart-widget"),
            md=6,
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Tendencia Semanal (% Sobre-tocados)"),
                dbc.CardBody(dcc.Loading(dcc.Graph(
                    id="tq-trend-chart", config={"displayModeBar": False},
                ))),
            ], className="chart-widget"),
            md=6,
        ),
    ], className="mb-4 g-3"),

    # --- Over-touched contacts table + CSV ---
    html.Div("CONTACTOS SOBRE-TOCADOS", className="section-label mb-2"),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader([
                    "Usuarios con >4 mensajes/semana",
                    dbc.Button(
                        [html.I(className="bi bi-download me-1"), "Exportar CSV"],
                        id="tq-export-csv-btn",
                        outline=True, color="secondary", size="sm",
                        className="float-end",
                    ),
                ]),
                dbc.CardBody(dcc.Loading(
                    dash_table.DataTable(
                        id="tq-contacts-table",
                        sort_action="native",
                        filter_action="native",
                        page_size=15,
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
            md=12,
        ),
    ], className="mb-4"),

    # Download component
    dcc.Download(id="tq-download-csv"),
], fluid=True, className="py-4")
