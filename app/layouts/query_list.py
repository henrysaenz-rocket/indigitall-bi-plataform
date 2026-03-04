"""Query list page — Browse all saved queries with search, favorites, thumbnails."""

import dash
from dash import html, dcc
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
        dbc.Col(dbc.Input(
            id="query-search-input",
            placeholder="Buscar consultas...",
            type="search",
            debounce=True,
            className="search-input",
        ), width=4),
        dbc.Col(dbc.ButtonGroup([
            dbc.Button([html.I(className="bi bi-star me-1"), "Favoritos"],
                       id="query-favorites-btn",
                       outline=True, color="secondary", size="sm"),
            dbc.Button("Todas",
                       id="query-all-btn",
                       outline=True, color="secondary", size="sm", active=True),
        ]), width="auto"),
    ], className="mb-4 align-items-center"),

    # Query list container
    html.Div(id="query-list-container"),
], fluid=True, className="py-4")
