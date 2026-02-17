"""Query list page callbacks — search, filter, pagination."""

from dash import Input, Output, State, callback, html, no_update
import dash_bootstrap_components as dbc

from app.services.storage_service import StorageService
from app.config import settings


def _query_row(q):
    """Render a single query row in the list."""
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.I(
                            className="bi bi-star-fill text-warning me-2",
                        ) if q.get("is_favorite") else html.I(className="bi bi-star me-2 text-muted"),
                        html.A(
                            q["name"],
                            href=f"/consultas/{q['id']}",
                            className="fw-semibold text-decoration-none",
                        ),
                    ]),
                    html.Small(
                        q.get("query_text", "")[:100],
                        className="text-muted d-block mt-1",
                    ),
                ], md=6),
                dbc.Col([
                    html.Small(q.get("ai_function") or "SQL", className="badge bg-light text-dark"),
                ], md=2, className="text-center"),
                dbc.Col([
                    html.Small(f"{q.get('result_row_count', 0)} filas", className="text-muted"),
                ], md=2, className="text-center"),
                dbc.Col([
                    html.Small(q.get("created_by") or "—", className="text-muted"),
                ], md=2, className="text-end"),
            ], className="align-items-center"),
        ], className="py-2"),
    ], className="mb-2")


@callback(
    Output("query-list-container", "children"),
    Input("tenant-context", "data"),
)
def load_query_list(tenant):
    svc = StorageService(tenant_id=tenant or settings.DEFAULT_TENANT)
    result = svc.list_queries(limit=50)

    if not result["queries"]:
        return html.Div([
            html.I(className="bi bi-search display-4 text-muted"),
            html.P("Aun no hay consultas guardadas. Crea tu primera consulta con el asistente IA.",
                   className="text-muted mt-3"),
            dbc.Button(
                [html.I(className="bi bi-plus-lg me-1"), "Nueva Consulta"],
                href="/consultas/nueva", color="primary", className="mt-2",
            ),
        ], className="text-center py-5")

    # Header row
    header = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col(html.Small("Nombre", className="fw-bold text-muted"), md=6),
                dbc.Col(html.Small("Tipo", className="fw-bold text-muted"), md=2, className="text-center"),
                dbc.Col(html.Small("Filas", className="fw-bold text-muted"), md=2, className="text-center"),
                dbc.Col(html.Small("Creado por", className="fw-bold text-muted"), md=2, className="text-end"),
            ]),
        ], className="py-1"),
    ], className="mb-2 bg-light")

    rows = [header] + [_query_row(q) for q in result["queries"]]
    rows.append(html.Small(f"Mostrando {len(result['queries'])} de {result['total']}", className="text-muted"))

    return html.Div(rows)
