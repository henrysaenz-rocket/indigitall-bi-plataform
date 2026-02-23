"""Data Explorer page — Browse database tables, schemas, and data previews."""

import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/datos", name="Datos", order=5)

layout = dbc.Container([
    # Page header
    html.H2([html.I(className="bi bi-database me-2"), "Datos"], className="page-title"),
    html.P("Explora las tablas de la base de datos, esquemas y vista previa de datos.",
           className="page-subtitle"),

    # Sync Status banner
    html.Div(id="de-sync-banner", className="mb-4"),

    # Table grid
    html.Div([
        html.H5([html.I(className="bi bi-table me-2"), "Tablas"], className="section-label mb-3"),
        dbc.Row(id="de-table-grid", className="g-3"),
    ], className="mb-4"),

    # Hidden store for selected table
    dcc.Store(id="de-selected-table", storage_type="memory"),

    # Detail panel (shown when a table is selected)
    html.Div(id="de-detail-panel", style={"display": "none"}, children=[
        # Table header
        html.Div(id="de-detail-header", className="mb-3"),

        # Tabs: Schema / Preview / Profile
        dbc.Tabs(id="de-detail-tabs", active_tab="tab-esquema", children=[
            dbc.Tab(label="Esquema", tab_id="tab-esquema", children=[
                html.Div(id="de-schema-content", className="mt-3"),
            ]),
            dbc.Tab(label="Vista Previa", tab_id="tab-preview", children=[
                html.Div(id="de-preview-content", className="mt-3"),
            ]),
            dbc.Tab(label="Perfil", tab_id="tab-profile", children=[
                html.Div(id="de-profile-content", className="mt-3"),
            ]),
        ]),
    ]),

], fluid=True, className="py-4")
