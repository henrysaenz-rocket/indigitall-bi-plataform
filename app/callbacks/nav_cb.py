"""Navbar callbacks — tenant selector population."""

from dash import Input, Output, callback
from app.services.data_service import DataService


@callback(
    Output("tenant-selector", "options"),
    Output("tenant-selector", "value"),
    Input("tenant-context", "data"),
)
def populate_tenant_selector(current_tenant):
    """Populate the tenant dropdown with available entities."""
    svc = DataService()
    entities = svc.get_entities()

    options = [{"label": e, "value": e} for e in entities]

    # Set default value to current tenant if it exists in the list
    value = current_tenant if current_tenant in entities else (entities[0] if entities else None)

    return options, value


@callback(
    Output("tenant-context", "data"),
    Input("tenant-selector", "value"),
    prevent_initial_call=True,
)
def update_tenant_context(selected_tenant):
    """Update the global tenant context when selector changes."""
    return selected_tenant
