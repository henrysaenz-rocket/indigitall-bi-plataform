"""Dashboard Unificado — Single dashboard with channel tabs."""

import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/tableros", name="Tableros", order=3)

# Prefix: ud- (unified dashboard)

TABLE_STYLE = {
    "cell": {
        "textAlign": "left", "padding": "8px",
        "fontFamily": "Inter, sans-serif", "fontSize": "13px",
    },
    "header": {
        "backgroundColor": "#F5F7FA", "fontWeight": "600",
        "border": "1px solid #E4E4E7",
    },
    "data": {"border": "1px solid #E4E4E7"},
    "conditional": [{"if": {"row_index": "odd"}, "backgroundColor": "#FAFBFC"}],
}


def _chart_card(title, graph_id, md=6):
    return dbc.Col(
        dbc.Card([
            dbc.CardHeader(title),
            dbc.CardBody(dcc.Loading(dcc.Graph(
                id=graph_id, config={"displayModeBar": False},
            ))),
        ], className="chart-widget"),
        md=md,
    )


def _data_table(table_id, page_size=10, filterable=False):
    return dash_table.DataTable(
        id=table_id,
        sort_action="native",
        filter_action="native" if filterable else "none",
        page_size=page_size,
        style_table={"overflowX": "auto"},
        style_cell=TABLE_STYLE["cell"],
        style_header=TABLE_STYLE["header"],
        style_data=TABLE_STYLE["data"],
        style_data_conditional=TABLE_STYLE["conditional"],
    )


# ===================== Tab Builders =====================

def _build_toques_tab():
    return dbc.Tab(label="Control Toques", tab_id="tab-toques", children=[
        html.Div("RESUMEN DE TOQUES", className="section-label mb-2 mt-3"),
        dbc.Row(id="ud-tq-kpi-row", className="mb-4 g-3"),
        html.Div("DISTRIBUCION Y TENDENCIA", className="section-label mb-2"),
        dbc.Row([
            _chart_card("Mensajes por Contacto/Semana", "ud-tq-distribution-chart"),
            _chart_card("Tendencia Semanal (% Sobre-tocados)", "ud-tq-trend-chart"),
        ], className="mb-4 g-3"),
        html.Div("CONTACTOS SOBRE-TOCADOS", className="section-label mb-2"),
        dbc.Row([dbc.Col(
            dbc.Card([
                dbc.CardHeader([
                    "Usuarios con >4 mensajes/semana",
                    dbc.Button(
                        [html.I(className="bi bi-download me-1"), "Exportar CSV"],
                        id="ud-tq-export-csv-btn", outline=True,
                        color="secondary", size="sm", className="float-end",
                    ),
                ]),
                dbc.CardBody(dcc.Loading(_data_table(
                    "ud-tq-contacts-table", page_size=15, filterable=True,
                ))),
            ], className="chart-widget"), md=12,
        )], className="mb-4"),
        dcc.Download(id="ud-tq-download-csv"),
    ])


def _build_sms_tab():
    return dbc.Tab(label="SMS", tab_id="tab-sms", children=[
        html.Div("RESUMEN SMS", className="section-label mb-2 mt-3"),
        dbc.Row(id="ud-sms-kpi-row", className="mb-4 g-3"),
        html.Div("TENDENCIA DE ENVIOS", className="section-label mb-2"),
        dbc.Row([
            _chart_card("Enviados vs Chunks", "ud-sms-sends-chunks-chart"),
            _chart_card("Enviados vs Clicks vs CTR", "ud-sms-sends-clicks-chart"),
        ], className="mb-4 g-3"),
        html.Div("PATRONES Y RANKING", className="section-label mb-2"),
        dbc.Row([
            _chart_card("Mapa de Calor (Hora/Dia)", "ud-sms-heatmap-chart"),
            _chart_card("Ranking Campanas por Volumen", "ud-sms-ranking-chart"),
        ], className="mb-4 g-3"),
    ])


def _build_email_tab():
    return dbc.Tab(label="Email", tab_id="tab-email", children=[
        html.Div("RESUMEN EMAIL", className="section-label mb-2 mt-3"),
        dbc.Row(id="ud-email-kpi-row", className="mb-4 g-3"),
        html.Div("ENGAGEMENT", className="section-label mb-2"),
        dbc.Row([
            _chart_card("Entregados vs Abiertos vs Clicks", "ud-email-engagement-chart", md=8),
            _chart_card("Desglose de Errores", "ud-email-errors-chart", md=4),
        ], className="mb-4 g-3"),
        html.Div("PATRONES Y RANKING", className="section-label mb-2"),
        dbc.Row([
            _chart_card("Mapa de Calor Apertura", "ud-email-heatmap-chart"),
            _chart_card("Ranking Campanas por Engagement", "ud-email-ranking-chart"),
        ], className="mb-4 g-3"),
    ])


def _build_push_tab():
    return dbc.Tab(label="Push", tab_id="tab-push", children=[
        html.Div("RESUMEN PUSH", className="section-label mb-2 mt-3"),
        dbc.Row(id="ud-push-kpi-row", className="mb-4 g-3"),
        html.Div("TENDENCIA Y PATRONES", className="section-label mb-2"),
        dbc.Row([
            _chart_card("Enviados vs Clicks vs CTR", "ud-push-trend-chart"),
            _chart_card("Mapa de Calor (Hora/Dia)", "ud-push-heatmap-chart"),
        ], className="mb-4 g-3"),
    ])


def _build_inapp_tab():
    return dbc.Tab(label="In App/Web", tab_id="tab-inapp", children=[
        html.Div("RESUMEN IN APP/WEB", className="section-label mb-2 mt-3"),
        dbc.Row(id="ud-inapp-kpi-row", className="mb-4 g-3"),
        html.Div("ENGAGEMENT Y CONVERSION", className="section-label mb-2"),
        dbc.Row([
            _chart_card("Impresiones vs Clicks", "ud-inapp-engagement-chart"),
            _chart_card("Funnel de Conversion", "ud-inapp-funnel-chart"),
        ], className="mb-4 g-3"),
    ])


def _build_cc_tab():
    return dbc.Tab(label="Contact Center", tab_id="tab-cc", children=[
        html.Div("RESUMEN CONTACT CENTER", className="section-label mb-2 mt-3"),
        dbc.Row(id="ud-cc-kpi-row", className="mb-4 g-3"),
        html.Div("VOLUMEN DE CONVERSACIONES", className="section-label mb-2"),
        dbc.Row([
            _chart_card("Conversaciones por Dia", "ud-cc-conv-trend-chart", md=8),
            _chart_card("Distribucion de Espera", "ud-cc-wait-chart", md=4),
        ], className="mb-4 g-3"),
        html.Div("AGENTES Y RAZONES DE CIERRE", className="section-label mb-2"),
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Top Agentes"),
                    dbc.CardBody(dcc.Loading(_data_table("ud-cc-agent-table"))),
                ], className="chart-widget"), md=7,
            ),
            _chart_card("Razones de Cierre", "ud-cc-close-reasons-chart", md=5),
        ], className="mb-4 g-3"),
        html.Div("DISTRIBUCION HORARIA", className="section-label mb-2"),
        dbc.Row([
            _chart_card("Conversaciones por Hora", "ud-cc-hourly-chart", md=12),
        ], className="mb-4"),
    ])


def _build_bot_tab():
    return dbc.Tab(label="Bot", tab_id="tab-bot", children=[
        html.Div("RESUMEN BOT", className="section-label mb-2 mt-3"),
        dbc.Row(id="ud-bot-kpi-row", className="mb-4 g-3"),
        html.Div("AUTOMATIZACION VS HUMANO", className="section-label mb-2"),
        dbc.Row([
            _chart_card("Bot vs Agente", "ud-bot-vs-human-chart", md=4),
            _chart_card("Tendencia de Fallback", "ud-bot-fallback-chart", md=8),
        ], className="mb-4 g-3"),
        html.Div("INTENCIONES Y CONTENIDO", className="section-label mb-2"),
        dbc.Row([
            _chart_card("Top Intenciones", "ud-bot-intents-chart", md=7),
            _chart_card("Tipos de Contenido", "ud-bot-content-chart", md=5),
        ], className="mb-4 g-3"),
    ])


# ===================== Main Layout =====================

layout = dbc.Container([
    html.H2("Dashboard Analitico", className="page-title"),
    html.P(
        "Vista unificada de todos los canales — Visionamos",
        className="page-subtitle",
    ),

    # --- Date selector ---
    dbc.Row([
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button("7D", id="ud-btn-7d", outline=True,
                           color="primary", size="sm"),
                dbc.Button("30D", id="ud-btn-30d", outline=True,
                           color="primary", size="sm", active=True),
                dbc.Button("90D", id="ud-btn-90d", outline=True,
                           color="primary", size="sm"),
                dbc.Button("Custom", id="ud-btn-custom", outline=True,
                           color="primary", size="sm"),
            ]),
            dcc.DatePickerRange(
                id="ud-date-picker",
                display_format="YYYY-MM-DD",
                style={"display": "none"},
                className="ms-3",
            ),
        ], className="d-flex align-items-center"),
    ], className="mb-4"),

    dcc.Store(id="ud-date-store", storage_type="session"),

    # --- Tabs ---
    dbc.Tabs(
        id="ud-tabs",
        active_tab="tab-toques",
        className="ud-tabs",
        children=[
            _build_toques_tab(),
            _build_sms_tab(),
            _build_email_tab(),
            _build_push_tab(),
            _build_inapp_tab(),
            _build_cc_tab(),
            _build_bot_tab(),
        ],
    ),
], fluid=True, className="py-4")
