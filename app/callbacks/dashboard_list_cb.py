"""Dashboard list page callbacks — load, search, filter."""

from dash import Input, Output, callback, html
import dash_bootstrap_components as dbc

from app.services.storage_service import StorageService
from app.config import settings


def _dashboard_row(d):
    """Render a single dashboard row."""
    layout = d.get("layout") or []
    widget_count = len(layout) if isinstance(layout, list) else 0

    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.I(
                            className="bi bi-star-fill text-warning me-2",
                        ) if d.get("is_favorite") else html.I(className="bi bi-star me-2 text-muted"),
                        html.A(
                            d["name"],
                            href=f"/tableros/{d['id']}",
                            className="fw-semibold text-decoration-none",
                        ),
                        html.Span(
                            " (Principal)",
                            className="badge bg-primary ms-2",
                        ) if d.get("is_default") else None,
                    ]),
                ], md=5),
                dbc.Col([
                    html.Small(f"{widget_count} widgets", className="text-muted"),
                ], md=2, className="text-center"),
                dbc.Col([
                    html.Small(d.get("created_by") or "—", className="text-muted"),
                ], md=2, className="text-center"),
                dbc.Col([
                    html.Small(
                        str(d.get("updated_at", ""))[:10] if d.get("updated_at") else "—",
                        className="text-muted",
                    ),
                ], md=3, className="text-end"),
            ], className="align-items-center"),
        ], className="py-2"),
    ], className="mb-2")


@callback(
    Output("dashboard-list-container", "children"),
    Input("tenant-context", "data"),
)
def load_dashboard_list(tenant):
    svc = StorageService(tenant_id=tenant or settings.DEFAULT_TENANT)
    result = svc.list_dashboards(limit=50)

    if not result["dashboards"]:
        return html.Div([
            html.I(className="bi bi-grid-1x2 display-4 text-muted"),
            html.P("Aun no hay tableros. Crea tu primer tablero y agrega widgets desde tus consultas.",
                   className="text-muted mt-3"),
            dbc.Button(
                [html.I(className="bi bi-plus-lg me-1"), "Nuevo Tablero"],
                href="/tableros/nuevo", color="primary", className="mt-2",
            ),
        ], className="text-center py-5")

    header = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col(html.Small("Nombre", className="fw-bold text-muted"), md=5),
                dbc.Col(html.Small("Widgets", className="fw-bold text-muted"), md=2, className="text-center"),
                dbc.Col(html.Small("Creado por", className="fw-bold text-muted"), md=2, className="text-center"),
                dbc.Col(html.Small("Actualizado", className="fw-bold text-muted"), md=3, className="text-end"),
            ]),
        ], className="py-1"),
    ], className="mb-2 bg-light")

    rows = [header] + [_dashboard_row(d) for d in result["dashboards"]]
    rows.append(html.Small(f"Mostrando {len(result['dashboards'])} de {result['total']}", className="text-muted"))

    return html.Div(rows)
