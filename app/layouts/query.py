"""Query page — AI chat (left) + Results (right)."""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/consultas/nueva", name="Nueva Consulta", order=1)

# Suggestion chips (common questions in Spanish)
SUGGESTIONS = [
    "Dame un resumen general de los datos",
    "Cual es la tasa de fallback?",
    "Mensajes por hora del dia",
    "Top 10 contactos mas activos",
    "Rendimiento de agentes",
    "Comparacion entre entidades",
    "Distribucion de intenciones",
    "Mensajes por dia de la semana",
    "Tendencia de mensajes en el tiempo",
]

layout = dbc.Container([
    dbc.Row([
        # Left panel: AI Chat (35%)
        dbc.Col([
            html.Div([
                html.H5([html.I(className="bi bi-chat-dots me-2"), "Asistente IA"],
                         className="panel-title"),

                # Suggestion chips (shown when no messages)
                html.Div(
                    [dbc.Button(s, outline=True, color="primary", size="sm",
                                className="suggestion-chip me-2 mb-2")
                     for s in SUGGESTIONS],
                    id="suggestion-chips",
                    className="mb-3",
                ),

                # Chat messages container
                html.Div(id="chat-messages", className="chat-messages-container"),

                # Chat input
                dbc.InputGroup([
                    dbc.Input(
                        id="chat-input",
                        placeholder="Haz una pregunta sobre tus datos...",
                        type="text",
                        className="chat-input-field",
                    ),
                    dbc.Button(
                        html.I(className="bi bi-send"),
                        id="chat-send-btn",
                        color="primary",
                        className="chat-send-btn",
                    ),
                ], className="chat-input-group"),
            ], className="chat-panel"),
        ], width=5, className="chat-column"),

        # Right panel: Results (65%)
        dbc.Col([
            html.Div([
                html.Div([
                    html.H5("Resultados", className="panel-title"),
                    html.Div([
                        dbc.Button([html.I(className="bi bi-download me-1"), "CSV"],
                                   outline=True, color="secondary", size="sm",
                                   className="me-2", id="download-csv-btn", disabled=True),
                        dbc.Button([html.I(className="bi bi-bookmark me-1"), "Guardar"],
                                   color="primary", size="sm",
                                   id="save-query-btn", disabled=True),
                    ]),
                ], className="d-flex justify-content-between align-items-center mb-3"),

                # Results placeholder
                html.Div([
                    html.Div([
                        html.I(className="bi bi-chat-square-text display-4 text-muted"),
                        html.P("Los resultados de tu consulta apareceran aqui.",
                               className="text-muted mt-3"),
                    ], className="text-center py-5"),
                ], id="results-container", className="results-panel"),

            ], className="results-wrapper"),
        ], width=7, className="results-column"),
    ], className="g-3 query-page-row"),

    # Download component
    dcc.Download(id="download-csv"),

], fluid=True, className="py-3 query-page")
