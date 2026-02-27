"""Dashboard view page — Widget grid display."""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(
    __name__,
    path_template="/tableros/saved/<dashboard_id>",
    name="Tablero",
    order=39,
)


def layout(dashboard_id=None, **kwargs):
    return dbc.Container([
        # Dashboard header
        html.Div([
            html.Div([
                html.H2(f"Tablero #{dashboard_id}" if dashboard_id else "Tablero",
                         className="page-title mb-0"),
                html.Small("Cargando...", className="text-muted"),
            ]),
            html.Div([
                dbc.Button([html.I(className="bi bi-pencil me-1"), "Editar"],
                           outline=True, color="secondary", size="sm", className="me-2"),
                dbc.Button([html.I(className="bi bi-share me-1"), "Compartir"],
                           outline=True, color="secondary", size="sm", className="me-2"),
                dbc.Button(html.I(className="bi bi-star"), outline=True,
                           color="warning", size="sm"),
            ]),
        ], className="d-flex justify-content-between align-items-start mb-4"),

        # Widget grid placeholder
        html.Div([
            html.Div([
                html.I(className="bi bi-grid-1x2 display-4 text-muted"),
                html.P("Agrega widgets a este tablero desde tus consultas guardadas.",
                       className="text-muted mt-3"),
            ], className="text-center py-5"),
        ], id="dashboard-grid", className="dashboard-grid"),

        # Floating AI chat button
        dbc.Button(
            [html.I(className="bi bi-chat-dots me-1"), "Preguntar"],
            id="open-ai-chat",
            color="primary",
            className="fab-chat-btn",
        ),

        # AI Chat slide-over (Offcanvas)
        dbc.Offcanvas(
            html.Div("Chat IA integrado — proximamente.", className="p-3 text-muted"),
            id="ai-chat-offcanvas",
            title="Asistente IA",
            placement="end",
            style={"width": "400px"},
        ),
    ], fluid=True, className="py-4")
