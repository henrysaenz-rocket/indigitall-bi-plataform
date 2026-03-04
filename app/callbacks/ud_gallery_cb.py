"""Unified Dashboard — Gallery toggle + dynamic custom dashboards."""

from dash import Input, Output, callback, ctx, html
import dash_bootstrap_components as dbc

from app.services.storage_service import StorageService
from app.config import settings


@callback(
    Output("ud-gallery", "style"),
    Output("ud-dashboard", "style"),
    Input("ud-gallery-card-visionamos", "n_clicks"),
    Input("ud-back-to-gallery", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_gallery_dashboard(card_clicks, back_clicks):
    if ctx.triggered_id == "ud-gallery-card-visionamos":
        return {"display": "none"}, {"display": "block"}
    return {"display": "block"}, {"display": "none"}


def _format_date(dt):
    if not dt:
        return ""
    if hasattr(dt, "strftime"):
        return dt.strftime("%d %b %Y")
    return str(dt)[:10]


@callback(
    Output("custom-dashboards-grid", "children"),
    Input("tenant-context", "data"),
)
def load_custom_dashboards(tenant):
    svc = StorageService(tenant_id=tenant or settings.DEFAULT_TENANT)
    result = svc.list_dashboards(limit=20)

    if not result["dashboards"]:
        return html.Div([
            html.Small("No hay tableros personalizados. Crea uno con el constructor.",
                       className="text-muted"),
        ], className="text-center py-3")

    cards = []
    for d in result["dashboards"]:
        widget_count = 0
        if d.get("layout"):
            # layout is stored separately, count from list_dashboards doesn't include it
            widget_count = "—"

        cards.append(
            dbc.Col(
                html.A(
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="bi bi-grid-1x2",
                                       style={"fontSize": "24px", "color": "#1E88E5"}),
                                html.I(className="bi bi-star-fill text-warning ms-auto",
                                       style={"fontSize": "14px"})
                                if d.get("is_favorite") else html.Span(),
                            ], className="d-flex align-items-start mb-2"),
                            html.H6(d["name"], style={"fontWeight": "600", "color": "#1A1A2E"}),
                            html.Small(
                                d.get("description") or "Tablero personalizado",
                                className="text-muted d-block",
                                style={"fontSize": "12px"},
                            ),
                            html.Div([
                                html.Small(
                                    _format_date(d.get("created_at")),
                                    className="text-muted",
                                    style={"fontSize": "11px"},
                                ),
                            ], className="mt-2"),
                        ], style={"padding": "20px"}),
                    ], style={
                        "borderRadius": "16px", "cursor": "pointer",
                        "border": "1px solid #E4E4E7",
                        "transition": "all 0.2s ease",
                    }, className="hover-shadow h-100"),
                    href=f"/tableros/saved/{d['id']}",
                    className="text-decoration-none",
                ),
                md=4, sm=6, xs=12,
            )
        )

    return dbc.Row(cards, className="g-3")
