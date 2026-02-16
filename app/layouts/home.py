"""Home page — Favorites + Recents (Redash-style landing)."""

import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/", name="Inicio", order=0)

layout = dbc.Container([
    html.H2("Bienvenido", className="page-title"),
    html.P("Tu plataforma de analytics con asistente de IA.", className="page-subtitle"),

    # Favorites section
    html.Div([
        html.H5([html.I(className="bi bi-star me-2"), "Favoritos"], className="section-label"),
        html.P("Marca consultas y tableros como favoritos para verlos aqui.",
               className="text-muted empty-state-text"),
    ], className="mb-4"),

    # Recent queries section
    html.Div([
        html.H5([html.I(className="bi bi-clock-history me-2"), "Consultas Recientes"], className="section-label"),
        html.P("Tus consultas recientes apareceran aqui.",
               className="text-muted empty-state-text"),
    ], className="mb-4"),

    # Recent dashboards section
    html.Div([
        html.H5([html.I(className="bi bi-grid-1x2 me-2"), "Tableros Recientes"], className="section-label"),
        html.P("Tus tableros recientes apareceran aqui.",
               className="text-muted empty-state-text"),
    ]),
], fluid=True, className="py-4")
