"""
Query page callbacks — AI chat interaction, results rendering, save/export.

This is the core interaction page: user asks questions in the chat panel,
AI processes them, results appear in the right panel with table + chart.
"""

import json
from datetime import datetime

import pandas as pd
from dash import (
    Input, Output, State, callback, html, dcc, no_update, ctx,
    ALL, MATCH,
)
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import plotly.express as px

from app.services.data_service import DataService
from app.services.storage_service import StorageService
from app.config import settings

# Chart color sequence from design system
CHART_COLORS = ["#1E88E5", "#76C043", "#A0A3BD", "#42A5F5", "#1565C0", "#FFC107", "#9C27B0", "#FF5722"]


def _render_user_message(text):
    return html.Div([
        html.Div(text, className="chat-message user-msg"),
    ], className="mb-3")


def _render_assistant_message(text):
    return html.Div([
        html.Div([
            html.I(className="bi bi-robot me-2"),
            html.Span(text),
        ], className="chat-message assistant-msg"),
    ], className="mb-3")


def _auto_chart(df, chart_type=None):
    """Generate a simple chart from a DataFrame based on its shape."""
    if df.empty or len(df.columns) < 2:
        return None

    x_col = df.columns[0]
    y_col = df.columns[1]

    # Heuristic: if x looks like a date, use line chart
    if chart_type == "line" or "date" in x_col.lower() or "fecha" in x_col.lower():
        fig = px.line(df, x=x_col, y=y_col, color_discrete_sequence=CHART_COLORS)
    elif chart_type == "pie" or len(df) <= 8:
        fig = px.pie(df, names=x_col, values=y_col, color_discrete_sequence=CHART_COLORS)
    elif chart_type == "bar" or df[y_col].dtype in ("int64", "float64"):
        fig = px.bar(df, x=x_col, y=y_col, color_discrete_sequence=CHART_COLORS)
    else:
        fig = px.bar(df, x=x_col, y=y_col, color_discrete_sequence=CHART_COLORS)

    fig.update_layout(
        template="plotly_white",
        font_family="Inter, sans-serif",
        margin=dict(l=20, r=20, t=30, b=20),
        height=350,
    )
    return fig


def _process_query(query_text, tenant, chat_history):
    """
    Process a user query using the demo pre-built functions.
    In Phase 4, this will be replaced by the AI agent (Claude Sonnet).
    """
    svc = DataService()
    query_lower = query_text.lower()

    # Simple keyword matching for demo (will be replaced by AI agent)
    if any(w in query_lower for w in ["resumen", "summary", "general", "estadisticas"]):
        stats = svc.get_summary_stats(tenant)
        df = pd.DataFrame([stats])
        explanation = (
            f"Total de mensajes: {stats['total_messages']:,}, "
            f"Contactos unicos: {stats['unique_contacts']:,}, "
            f"Agentes activos: {stats['active_agents']:,}, "
            f"Conversaciones: {stats['total_conversations']:,}."
        )
        return explanation, df, "summary", None

    elif any(w in query_lower for w in ["fallback", "tasa"]):
        result = svc.get_fallback_rate(tenant)
        df = pd.DataFrame([{"Metrica": "Tasa de Fallback", "Valor": f"{result['rate']}%",
                            "Fallbacks": result["fallback_count"], "Total": result["total"]}])
        explanation = f"La tasa de fallback es {result['rate']}% ({result['fallback_count']} de {result['total']} mensajes)."
        return explanation, df, "fallback_rate", None

    elif any(w in query_lower for w in ["hora", "hour", "horario"]):
        df = svc.get_messages_by_hour(tenant)
        return "Distribucion de mensajes por hora del dia:", df, "messages_by_hour", "bar"

    elif any(w in query_lower for w in ["direction", "direccion", "canal", "tipo"]):
        df = svc.get_messages_by_direction(tenant)
        return "Distribucion de mensajes por direccion:", df, "messages_by_direction", "pie"

    elif any(w in query_lower for w in ["tendencia", "tiempo", "trend", "over time"]):
        df = svc.get_messages_over_time(tenant)
        return "Tendencia de mensajes en el tiempo:", df, "messages_over_time", "line"

    elif any(w in query_lower for w in ["contacto", "contact", "top", "activo"]):
        df = svc.get_top_contacts(tenant, limit=10)
        return "Top 10 contactos mas activos:", df, "top_contacts", "bar"

    elif any(w in query_lower for w in ["intent", "intencion", "distribucion"]):
        df = svc.get_intent_distribution(tenant, limit=10)
        return "Distribucion de las principales intenciones:", df, "intent_distribution", "bar"

    elif any(w in query_lower for w in ["agente", "agent", "rendimiento", "performance"]):
        df = svc.get_agent_performance(tenant)
        return "Rendimiento de agentes:", df, "agent_performance", "bar"

    elif any(w in query_lower for w in ["dia", "semana", "day", "week"]):
        df = svc.get_messages_by_day_of_week(tenant)
        return "Mensajes por dia de la semana:", df, "messages_by_day_of_week", "bar"

    elif any(w in query_lower for w in ["comparacion", "entidad", "entity", "cooperativa"]):
        # Entity comparison — get messages grouped by tenant
        df = svc.get_messages_dataframe(tenant)
        if not df.empty and "tenant_id" in df.columns:
            comparison = df.groupby("tenant_id").size().reset_index(name="count")
            return "Comparacion entre entidades:", comparison, "entity_comparison", "bar"
        return "No hay datos suficientes para comparar entidades.", pd.DataFrame(), None, None

    else:
        return (
            "No reconozco esa consulta. Intenta preguntar sobre: resumen, fallback, "
            "mensajes por hora, tendencia, contactos, intenciones, agentes, o comparacion de entidades.",
            pd.DataFrame(),
            None,
            None,
        )


# --- Main chat callback ---

@callback(
    Output("chat-messages", "children"),
    Output("results-container", "children"),
    Output("chat-input", "value"),
    Output("chat-history", "data"),
    Output("query-result", "data"),
    Output("download-csv-btn", "disabled"),
    Output("save-query-btn", "disabled"),
    Input("chat-send-btn", "n_clicks"),
    Input("chat-input", "n_submit"),
    State("chat-input", "value"),
    State("tenant-context", "data"),
    State("chat-history", "data"),
    prevent_initial_call=True,
)
def send_message(n_clicks, n_submit, message, tenant, history):
    if not message or not message.strip():
        raise PreventUpdate

    history = history or []

    # Add user message
    history.append({"role": "user", "content": message})

    # Process query
    explanation, df, ai_function, chart_type = _process_query(message, tenant, history)

    # Add assistant response
    assistant_entry = {
        "role": "assistant",
        "content": explanation,
        "has_data": not df.empty,
        "row_count": len(df),
        "ai_function": ai_function,
        "chart_type": chart_type,
    }
    history.append(assistant_entry)

    # Render chat messages
    chat_elements = []
    for msg in history:
        if msg["role"] == "user":
            chat_elements.append(_render_user_message(msg["content"]))
        else:
            chat_elements.append(_render_assistant_message(msg["content"]))

    # Render results panel
    results = []
    if not df.empty:
        # Chart (if applicable)
        fig = _auto_chart(df, chart_type)
        if fig:
            results.append(dcc.Graph(figure=fig, className="mb-3"))

        # Data table
        from dash import dash_table
        results.append(
            dash_table.DataTable(
                data=df.to_dict("records"),
                columns=[{"name": c, "id": c} for c in df.columns],
                page_size=15,
                style_table={"overflowX": "auto"},
                style_header={
                    "backgroundColor": "#F5F7FA",
                    "fontWeight": "600",
                    "fontSize": "13px",
                    "color": "#6E7191",
                    "textTransform": "uppercase",
                },
                style_cell={
                    "fontSize": "13px",
                    "fontFamily": "Inter, sans-serif",
                    "padding": "8px 12px",
                },
                style_data_conditional=[{
                    "if": {"row_index": "odd"},
                    "backgroundColor": "#FAFBFC",
                }],
            )
        )

        results.append(html.Small(f"{len(df)} filas", className="text-muted mt-2 d-block"))
    else:
        results.append(html.Div([
            html.I(className="bi bi-info-circle display-4 text-muted"),
            html.P(explanation, className="text-muted mt-3"),
        ], className="text-center py-5"))

    # Store query result for CSV export / save
    query_data = {
        "query_text": message,
        "ai_function": ai_function,
        "chart_type": chart_type,
        "data": df.to_dict("records") if not df.empty else [],
        "columns": list(df.columns) if not df.empty else [],
        "row_count": len(df),
        "explanation": explanation,
    }

    has_data = not df.empty
    return chat_elements, results, "", history, query_data, not has_data, not has_data


# --- Suggestion chips ---

@callback(
    Output("chat-input", "value", allow_duplicate=True),
    Output("chat-send-btn", "n_clicks"),
    [Input({"type": "suggestion-chip", "index": ALL}, "n_clicks")],
    State("chat-send-btn", "n_clicks"),
    prevent_initial_call=True,
)
def click_suggestion(chip_clicks, current_n):
    """When a suggestion chip is clicked, fill the input and trigger send."""
    if not any(chip_clicks):
        raise PreventUpdate

    # Find which chip was clicked
    triggered = ctx.triggered_id
    if triggered and isinstance(triggered, dict):
        idx = triggered["index"]
        from app.layouts.query import SUGGESTIONS
        if 0 <= idx < len(SUGGESTIONS):
            return SUGGESTIONS[idx], (current_n or 0) + 1

    raise PreventUpdate


# --- CSV Export ---

@callback(
    Output("download-csv", "data"),
    Input("download-csv-btn", "n_clicks"),
    State("query-result", "data"),
    prevent_initial_call=True,
)
def export_csv(n_clicks, query_data):
    if not query_data or not query_data.get("data"):
        raise PreventUpdate

    df = pd.DataFrame(query_data["data"])
    return dcc.send_data_frame(df.to_csv, "consulta_resultado.csv", index=False)


# --- Save Query ---

@callback(
    Output("save-query-btn", "children"),
    Input("save-query-btn", "n_clicks"),
    State("query-result", "data"),
    State("tenant-context", "data"),
    prevent_initial_call=True,
)
def save_query(n_clicks, query_data, tenant):
    if not query_data or not query_data.get("data"):
        raise PreventUpdate

    svc = StorageService(tenant_id=tenant or settings.DEFAULT_TENANT)
    df = pd.DataFrame(query_data["data"])

    name = query_data.get("query_text", "Consulta")[:80]
    result = svc.save_query(
        name=name,
        query_text=query_data["query_text"],
        data=df,
        ai_function=query_data.get("ai_function"),
        visualizations=[{"type": query_data.get("chart_type") or "table", "is_default": True}],
    )

    if result.get("success"):
        return [html.I(className="bi bi-check me-1"), "Guardado"]
    return [html.I(className="bi bi-bookmark me-1"), "Guardar"]
