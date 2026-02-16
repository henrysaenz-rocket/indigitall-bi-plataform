"""Dashboard list page — Browse all dashboards."""

import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/tableros", name="Tableros", order=4)

layout = dbc.Container([
    html.Div([
        html.H2("Tableros", className="page-title"),
        dbc.Button([html.I(className="bi bi-plus-lg me-1"), "Nuevo Tablero"],
                   href="/tableros/nuevo", color="primary"),
    ], className="d-flex justify-content-between align-items-center mb-4"),

    # Filters bar
    dbc.Row([
        dbc.Col(dbc.Input(placeholder="Buscar tableros...", type="search",
                          className="search-input"), width=4),
        dbc.Col(dbc.ButtonGroup([
            dbc.Button([html.I(className="bi bi-star me-1"), "Favoritos"],
                       outline=True, color="secondary", size="sm"),
            dbc.Button("Todos", outline=True, color="secondary", size="sm", active=True),
        ]), width="auto"),
    ], className="mb-4 align-items-center"),

    # Dashboard list placeholder
    html.Div([
        html.Div([
            html.I(className="bi bi-grid-1x2 display-4 text-muted"),
            html.P("Aun no hay tableros. Crea tu primer tablero y agrega widgets desde tus consultas.",
                   className="text-muted mt-3"),
            dbc.Button([html.I(className="bi bi-plus-lg me-1"), "Nuevo Tablero"],
                       href="/tableros/nuevo", color="primary", className="mt-2"),
        ], className="text-center py-5"),
    ], id="dashboard-list-container"),
], fluid=True, className="py-4")
