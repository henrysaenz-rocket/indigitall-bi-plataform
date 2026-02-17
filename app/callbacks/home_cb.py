"""Home page callbacks — KPIs, favorites, quick actions."""

from dash import Input, Output, callback, html, no_update
import dash_bootstrap_components as dbc

from app.services.data_service import DataService
from app.services.storage_service import StorageService
from app.config import settings


def _kpi_card(label, value, icon):
    return dbc.Col(
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className=f"bi {icon} me-2 text-primary"),
                    html.Span(label, className="kpi-label"),
                ]),
                html.Div(f"{value:,}", className="kpi-value mt-1"),
            ]),
        ], className="kpi-card"),
        md=3, sm=6,
    )


@callback(
    Output("home-kpi-row", "children"),
    Input("tenant-context", "data"),
)
def load_home_kpis(tenant):
    svc = DataService()
    stats = svc.get_summary_stats(tenant_filter=tenant)

    return [
        _kpi_card("Total Mensajes", stats["total_messages"], "bi-chat-left-text"),
        _kpi_card("Contactos Unicos", stats["unique_contacts"], "bi-people"),
        _kpi_card("Agentes Activos", stats["active_agents"], "bi-headset"),
        _kpi_card("Conversaciones", stats["total_conversations"], "bi-chat-dots"),
    ]


@callback(
    Output("home-favorite-queries", "children"),
    Input("tenant-context", "data"),
)
def load_favorite_queries(tenant):
    svc = StorageService(tenant_id=tenant or settings.DEFAULT_TENANT)
    result = svc.list_queries(favorites_only=True, limit=6)

    if not result["queries"]:
        return html.P(
            "Marca consultas como favoritas para verlas aqui.",
            className="text-muted",
        )

    cards = []
    for q in result["queries"]:
        cards.append(
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-star-fill text-warning me-2"),
                            html.Span(q["name"], className="fw-semibold"),
                        ]),
                        html.Small(
                            q.get("query_text", "")[:80] + "..." if len(q.get("query_text", "")) > 80 else q.get("query_text", ""),
                            className="text-muted d-block mt-1",
                        ),
                    ]),
                ], className="h-100"),
                md=4, sm=6, className="mb-2",
            )
        )
    return dbc.Row(cards, className="g-2")


@callback(
    Output("home-favorite-dashboards", "children"),
    Input("tenant-context", "data"),
)
def load_favorite_dashboards(tenant):
    svc = StorageService(tenant_id=tenant or settings.DEFAULT_TENANT)
    result = svc.list_dashboards(favorites_only=True, limit=6)

    if not result["dashboards"]:
        return html.P(
            "Marca tableros como favoritos para verlos aqui.",
            className="text-muted",
        )

    cards = []
    for d in result["dashboards"]:
        layout_len = len(d.get("layout", []) or [])
        cards.append(
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-star-fill text-warning me-2"),
                            html.Span(d["name"], className="fw-semibold"),
                        ]),
                        html.Small(
                            f"{layout_len} widgets",
                            className="text-muted d-block mt-1",
                        ),
                    ]),
                ], className="h-100"),
                md=4, sm=6, className="mb-2",
            )
        )
    return dbc.Row(cards, className="g-2")


@callback(
    Output("home-redirect", "pathname"),
    Input("quick-action-query", "n_clicks"),
    Input("quick-action-dashboard", "n_clicks"),
    Input("quick-action-queries", "n_clicks"),
    prevent_initial_call=True,
)
def quick_action_navigate(q_clicks, d_clicks, ql_clicks):
    from dash import ctx
    triggered = ctx.triggered_id
    if triggered == "quick-action-query":
        return "/consultas/nueva"
    elif triggered == "quick-action-dashboard":
        return "/tableros/nuevo"
    elif triggered == "quick-action-queries":
        return "/consultas"
    return no_update
