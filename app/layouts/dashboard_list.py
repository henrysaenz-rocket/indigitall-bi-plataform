"""Dashboard Gallery — Card grid for navigating to dashboards."""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/tableros", name="Tableros", order=3)

DASHBOARDS = [
    {
        "id": "visionamos",
        "title": "Dashboard Visionamos",
        "subtitle": "WhatsApp — Red Coopcentral / VirtualCoop",
        "icon": "bi-chat-left-text",
        "color": "#1E88E5",
        "sections": ["KPIs", "Tendencia", "Horarios", "Intenciones", "Agentes"],
        "href": "/tableros/visionamos",
        "available": True,
    },
    {
        "id": "contact-center",
        "title": "Contact Center",
        "subtitle": "Conversaciones, agentes y tiempos de espera",
        "icon": "bi-headset",
        "color": "#76C043",
        "sections": ["KPIs", "Agentes", "Espera", "Razones Cierre"],
        "href": "/tableros/contact-center",
        "available": True,
    },
    {
        "id": "bot-performance",
        "title": "Bot / Automatizacion",
        "subtitle": "Rendimiento del chatbot y tasa de fallback",
        "icon": "bi-robot",
        "color": "#42A5F5",
        "sections": ["Fallback", "Bot vs Humano", "Intenciones", "Contenido"],
        "href": "/tableros/bot-performance",
        "available": True,
    },
    {
        "id": "control-toques",
        "title": "Control de Toques",
        "subtitle": "Frecuencia de contacto por usuario/semana",
        "icon": "bi-bell",
        "color": "#FFC107",
        "sections": ["Sobre-tocados", "Distribucion", "Tendencia", "Export CSV"],
        "href": "/tableros/control-toques",
        "available": True,
    },
    {
        "id": "sms",
        "title": "SMS",
        "subtitle": "Canal SMS no habilitado en esta cuenta",
        "icon": "bi-phone",
        "color": "#A0A3BD",
        "sections": [],
        "href": None,
        "available": False,
    },
    {
        "id": "nps",
        "title": "NPS / Satisfaccion",
        "subtitle": "Endpoint de satisfaccion no disponible",
        "icon": "bi-emoji-smile",
        "color": "#A0A3BD",
        "sections": [],
        "href": None,
        "available": False,
    },
]


def _dashboard_card(dashboard):
    """Render a single dashboard card."""
    is_available = dashboard["available"]
    opacity = "1" if is_available else "0.45"
    cursor = "pointer" if is_available else "default"

    badges = [
        dbc.Badge(s, color="light", text_color="secondary", className="me-1 mb-1")
        for s in dashboard["sections"]
    ]

    status_badge = (
        dbc.Badge("Activo", color="success", className="ms-auto")
        if is_available
        else dbc.Badge("Sin Datos", color="secondary", className="ms-auto")
    )

    card_content = dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Div(
                    html.I(className=f"bi {dashboard['icon']}", style={"fontSize": "24px"}),
                    style={
                        "width": "48px", "height": "48px",
                        "borderRadius": "12px",
                        "backgroundColor": f"{dashboard['color']}15",
                        "color": dashboard["color"],
                        "display": "flex", "alignItems": "center", "justifyContent": "center",
                    },
                ),
                status_badge,
            ], className="d-flex align-items-start mb-3"),
            html.H5(dashboard["title"], className="mb-1", style={"fontWeight": "600"}),
            html.P(dashboard["subtitle"], className="text-muted small mb-3"),
            html.Div(badges) if badges else None,
        ]),
    ], className="kpi-card h-100", style={"opacity": opacity, "cursor": cursor})

    if is_available:
        return dbc.Col(
            dcc.Link(card_content, href=dashboard["href"], style={"textDecoration": "none"}),
            md=4, sm=6, xs=12, className="mb-3",
        )
    return dbc.Col(card_content, md=4, sm=6, xs=12, className="mb-3")


layout = dbc.Container([
    html.H2("Tableros", className="page-title"),
    html.P(
        "Selecciona un dashboard para explorar los datos",
        className="page-subtitle mb-4",
    ),
    dbc.Row([_dashboard_card(d) for d in DASHBOARDS], className="g-3"),
], fluid=True, className="py-4")
