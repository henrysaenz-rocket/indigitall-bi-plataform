"""Data Explorer callbacks — table list, schema, preview, profile, sync status."""

from dash import Input, Output, State, callback, html, no_update, ctx, ALL, MATCH
import dash_bootstrap_components as dbc
from dash import dash_table
import json

from app.services.schema_service import SchemaService


# ─── Load table grid on page load ───────────────────────────────────────

@callback(
    Output("de-table-grid", "children"),
    Input("tenant-context", "data"),
)
def load_table_grid(tenant):
    svc = SchemaService()
    tables = svc.list_tables()

    if not tables:
        return html.P("No se encontraron tablas.", className="text-muted")

    cards = []
    for t in tables:
        name = t["table_name"]
        cards.append(
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-table me-2 text-primary"),
                            html.Span(name, className="fw-semibold"),
                        ]),
                        html.Div([
                            dbc.Badge(f"{t['row_count']:,} filas", color="primary",
                                      className="me-2"),
                            dbc.Badge(t["size"], color="light", text_color="secondary"),
                        ], className="mt-2"),
                    ]),
                ], className="table-card h-100",
                   id={"type": "table-card", "index": name},
                   style={"cursor": "pointer"}),
                md=3, sm=6, xs=12,
            )
        )
    return cards


# ─── Handle table card click ────────────────────────────────────────────

@callback(
    Output("de-selected-table", "data"),
    Input({"type": "table-card", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def select_table(n_clicks_list):
    if not any(n_clicks_list):
        return no_update
    triggered = ctx.triggered_id
    if triggered and isinstance(triggered, dict):
        return triggered["index"]
    return no_update


# ─── Show/hide detail panel + load header ────────────────────────────────

@callback(
    Output("de-detail-panel", "style"),
    Output("de-detail-header", "children"),
    Input("de-selected-table", "data"),
)
def toggle_detail_panel(table_name):
    if not table_name:
        return {"display": "none"}, ""

    header = html.Div([
        html.H4([
            html.I(className="bi bi-table me-2"),
            table_name,
        ], className="panel-title mb-0"),
        dbc.Button(
            [html.I(className="bi bi-x-lg")],
            id="de-close-detail",
            color="light",
            size="sm",
            className="ms-auto",
        ),
    ], className="d-flex align-items-center")

    return {"display": "block"}, header


# ─── Load schema tab ─────────────────────────────────────────────────────

@callback(
    Output("de-schema-content", "children"),
    Input("de-selected-table", "data"),
    Input("de-detail-tabs", "active_tab"),
)
def load_schema(table_name, active_tab):
    if not table_name or active_tab != "tab-esquema":
        return no_update

    svc = SchemaService()
    columns = svc.get_table_schema(table_name)

    if not columns:
        return html.P("No se encontraron columnas.", className="text-muted")

    rows = []
    for col in columns:
        rows.append(html.Tr([
            html.Td(col["column_name"], className="fw-semibold"),
            html.Td(dbc.Badge(col["data_type"], color="info", className="text-uppercase")),
            html.Td(
                dbc.Badge("NULL", color="warning") if col["nullable"]
                else dbc.Badge("NOT NULL", color="secondary")
            ),
            html.Td(
                html.Code(col["default"][:40]) if col["default"] else
                html.Span("-", className="text-muted")
            ),
        ]))

    table = dbc.Table([
        html.Thead(html.Tr([
            html.Th("Columna"),
            html.Th("Tipo"),
            html.Th("Nullable"),
            html.Th("Default"),
        ])),
        html.Tbody(rows),
    ], bordered=True, hover=True, responsive=True, size="sm")

    # Also show indexes
    indexes = svc.get_table_indexes(table_name)
    idx_section = []
    if indexes:
        idx_rows = [
            html.Tr([html.Td(i["name"]), html.Td(html.Code(i["definition"][:80]))])
            for i in indexes
        ]
        idx_section = [
            html.H6([html.I(className="bi bi-lightning me-1"), "Indices"],
                     className="mt-4 mb-2"),
            dbc.Table([
                html.Thead(html.Tr([html.Th("Nombre"), html.Th("Definicion")])),
                html.Tbody(idx_rows),
            ], bordered=True, hover=True, responsive=True, size="sm"),
        ]

    return html.Div([table] + idx_section)


# ─── Load preview tab ─────────────────────────────────────────────────────

@callback(
    Output("de-preview-content", "children"),
    Input("de-selected-table", "data"),
    Input("de-detail-tabs", "active_tab"),
)
def load_preview(table_name, active_tab):
    if not table_name or active_tab != "tab-preview":
        return no_update

    svc = SchemaService()
    df = svc.preview_table(table_name, limit=50)

    if df.empty:
        return html.P("La tabla esta vacia.", className="text-muted")

    return html.Div([
        html.P(f"Mostrando {len(df)} de los primeros registros.", className="text-muted small mb-2"),
        dash_table.DataTable(
            data=df.astype(str).to_dict("records"),
            columns=[{"name": c, "id": c} for c in df.columns],
            page_size=15,
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": "#F5F7FA",
                "fontWeight": "600",
                "fontSize": "13px",
                "textTransform": "uppercase",
                "letterSpacing": "0.03em",
            },
            style_cell={
                "fontSize": "13px",
                "padding": "8px 12px",
                "maxWidth": "200px",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
            },
            style_data_conditional=[{
                "if": {"row_index": "odd"},
                "backgroundColor": "#FAFBFC",
            }],
        ),
    ])


# ─── Load profile tab ────────────────────────────────────────────────────

@callback(
    Output("de-profile-content", "children"),
    Input("de-selected-table", "data"),
    Input("de-detail-tabs", "active_tab"),
)
def load_profile(table_name, active_tab):
    if not table_name or active_tab != "tab-profile":
        return no_update

    svc = SchemaService()
    profile = svc.get_table_profile(table_name)

    if not profile:
        return html.P("No hay datos para perfilar.", className="text-muted")

    rows = []
    for col_stats in profile:
        total = col_stats.get("total_count", 0)
        null_pct = col_stats.get("null_pct", 0)
        distinct = col_stats.get("distinct_count", 0)

        # Color the null % bar
        if null_pct == 0:
            null_color = "success"
        elif null_pct < 20:
            null_color = "info"
        elif null_pct < 50:
            null_color = "warning"
        else:
            null_color = "danger"

        rows.append(html.Tr([
            html.Td(col_stats.get("column_name", ""), className="fw-semibold"),
            html.Td(f"{total:,}"),
            html.Td(f"{distinct:,}"),
            html.Td(
                html.Div([
                    dbc.Progress(value=float(null_pct), max=100, color=null_color,
                                 style={"height": "8px", "width": "60px"},
                                 className="d-inline-block me-2"),
                    html.Span(f"{null_pct}%", className="small"),
                ], className="d-flex align-items-center")
            ),
        ]))

    return dbc.Table([
        html.Thead(html.Tr([
            html.Th("Columna"),
            html.Th("Total"),
            html.Th("Distintos"),
            html.Th("% Nulos"),
        ])),
        html.Tbody(rows),
    ], bordered=True, hover=True, responsive=True, size="sm")


# ─── Load sync status banner ─────────────────────────────────────────────

@callback(
    Output("de-sync-banner", "children"),
    Input("tenant-context", "data"),
)
def load_sync_banner(tenant):
    svc = SchemaService()
    sync_rows = svc.get_sync_status()

    if not sync_rows:
        return dbc.Alert(
            [html.I(className="bi bi-info-circle me-2"),
             "No hay datos de sincronizacion. Ejecuta la ingesta para comenzar."],
            color="info",
            className="mb-0",
        )

    # Filter by tenant if set
    if tenant:
        sync_rows = [r for r in sync_rows if r["tenant_id"] == tenant]

    cards = []
    for s in sync_rows:
        status = s["status"]
        if status == "completed":
            badge_color = "success"
            icon = "bi-check-circle-fill"
        elif status == "running":
            badge_color = "primary"
            icon = "bi-arrow-repeat"
        elif status == "error":
            badge_color = "danger"
            icon = "bi-exclamation-triangle-fill"
        else:
            badge_color = "secondary"
            icon = "bi-clock"

        cards.append(
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className=f"bi {icon} me-2"),
                            html.Span(s["entity"].replace("_", " ").title(),
                                      className="fw-semibold"),
                        ]),
                        html.Div([
                            dbc.Badge(status, color=badge_color, className="me-2"),
                            html.Small(f"{s['records_synced']:,} registros",
                                       className="text-muted"),
                        ], className="mt-1"),
                        html.Small(f"Ultima sync: {s['last_sync_at']}",
                                   className="text-muted d-block mt-1"),
                    ], className="py-2 px-3"),
                ], className="sync-card"),
                md=3, sm=6, xs=12,
            )
        )

    return html.Div([
        html.H5([html.I(className="bi bi-arrow-repeat me-2"), "Estado de Sincronizacion"],
                 className="section-label mb-3"),
        dbc.Row(cards, className="g-2"),
    ])


# ─── Close detail panel ──────────────────────────────────────────────────

@callback(
    Output("de-selected-table", "data", allow_duplicate=True),
    Input("de-close-detail", "n_clicks"),
    prevent_initial_call=True,
)
def close_detail(n_clicks):
    return None
