"""Query list page — Browse all saved queries."""

import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/consultas", name="Consultas", order=2)

layout = dbc.Container([
    html.Div([
        html.H2("Consultas", className="page-title"),
        dbc.Button([html.I(className="bi bi-plus-lg me-1"), "Nueva Consulta"],
                   href="/consultas/nueva", color="primary"),
    ], className="d-flex justify-content-between align-items-center mb-4"),

    # Filters bar
    dbc.Row([
        dbc.Col(dbc.Input(placeholder="Buscar consultas...", type="search",
                          className="search-input"), width=4),
        dbc.Col(dbc.ButtonGroup([
            dbc.Button([html.I(className="bi bi-star me-1"), "Favoritos"],
                       outline=True, color="secondary", size="sm"),
            dbc.Button("Todas", outline=True, color="secondary", size="sm", active=True),
        ]), width="auto"),
    ], className="mb-4 align-items-center"),

    # Query list table placeholder
    html.Div([
        html.Div([
            html.I(className="bi bi-search display-4 text-muted"),
            html.P("Aun no hay consultas guardadas. Crea tu primera consulta con el asistente IA.",
                   className="text-muted mt-3"),
            dbc.Button([html.I(className="bi bi-plus-lg me-1"), "Nueva Consulta"],
                       href="/consultas/nueva", color="primary", className="mt-2"),
        ], className="text-center py-5"),
    ], id="query-list-container"),
], fluid=True, className="py-4")
