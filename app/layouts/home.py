"""Home page — KPI summary + Favorites + Quick actions."""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/", name="Inicio", order=0)

layout = dbc.Container([
    html.H2("Bienvenido", className="page-title"),
    html.P("Tu plataforma de analytics con asistente de IA.", className="page-subtitle"),

    # KPI cards row
    dbc.Row(id="home-kpi-row", className="mb-4 g-3"),

    # Quick actions
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.I(className="bi bi-chat-dots display-6 text-primary"),
                    html.H5("Nueva Consulta", className="mt-2 mb-1"),
                    html.P("Pregunta al asistente IA sobre tus datos",
                           className="text-muted small mb-0"),
                ]),
            ], className="h-100 text-center", style={"cursor": "pointer"},
               id="quick-action-query"),
            md=4,
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.I(className="bi bi-grid-1x2 display-6 text-primary"),
                    html.H5("Nuevo Tablero", className="mt-2 mb-1"),
                    html.P("Crea un tablero con tus consultas guardadas",
                           className="text-muted small mb-0"),
                ]),
            ], className="h-100 text-center", style={"cursor": "pointer"},
               id="quick-action-dashboard"),
            md=4,
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.I(className="bi bi-search display-6 text-primary"),
                    html.H5("Ver Consultas", className="mt-2 mb-1"),
                    html.P("Explora las consultas guardadas del equipo",
                           className="text-muted small mb-0"),
                ]),
            ], className="h-100 text-center", style={"cursor": "pointer"},
               id="quick-action-queries"),
            md=4,
        ),
    ], className="mb-4 g-3"),

    # Favorites section
    html.Div([
        html.H5([html.I(className="bi bi-star me-2"), "Consultas Favoritas"],
                 className="section-label"),
        html.Div(id="home-favorite-queries"),
    ], className="mb-4"),

    # Favorite dashboards
    html.Div([
        html.H5([html.I(className="bi bi-grid-1x2 me-2"), "Tableros Favoritos"],
                 className="section-label"),
        html.Div(id="home-favorite-dashboards"),
    ]),

    # Navigation links for quick actions
    dcc.Location(id="home-redirect", refresh=True),
], fluid=True, className="py-4")
