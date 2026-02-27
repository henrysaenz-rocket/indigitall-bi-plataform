"""Label Service — Maps technical column names to user-friendly Spanish labels."""

COLUMN_LABELS = {
    # Messages
    "message_count": "Cantidad de Mensajes",
    "count": "Total",
    "total": "Total",
    "direction": "Direccion",
    "contact_name": "Contacto",
    "contact_id": "ID Contacto",
    "agent_id": "Agente",
    "agent_email": "Email Agente",
    "conversation_id": "Conversacion",
    "hour": "Hora del Dia",
    "day_of_week": "Dia de la Semana",
    "date": "Fecha",
    "timestamp": "Fecha/Hora",
    "send_type": "Tipo de Envio",
    "content_type": "Tipo de Contenido",
    "status": "Estado",
    "intent": "Intencion",
    "is_fallback": "Es Fallback",
    "is_bot": "Es Bot",
    "is_human": "Es Humano",
    "message_body": "Mensaje",
    "close_reason": "Razon de Cierre",
    # Contacts
    "total_messages": "Total Mensajes",
    "first_contact": "Primer Contacto",
    "last_contact": "Ultimo Contacto",
    "total_conversations": "Total Conversaciones",
    "unique_contacts": "Contactos Unicos",
    # Agents
    "messages": "Mensajes",
    "conversations": "Conversaciones",
    "conversations_handled": "Conversaciones Atendidas",
    "avg_handle_seconds": "T. Gestion (s)",
    "avg_wait_seconds": "T. Espera (s)",
    "avg_handle_time_seconds": "T. Gestion Prom (s)",
    "wait_time_seconds": "T. Espera (s)",
    "handle_time_seconds": "T. Gestion (s)",
    "active_days": "Dias Activos",
    "active_agents": "Agentes Activos",
    # KPI / Summary
    "Metrica": "Metrica",
    "Valor": "Valor",
    "Porcentaje": "Porcentaje",
    "Estado": "Estado",
    "fallback_rate": "Tasa Fallback",
    "fallback_count": "Mensajes Fallback",
    # Chat Conversations
    "session_id": "ID Sesion",
    "channel": "Canal",
    "queued_at": "En Cola",
    "assigned_at": "Asignado",
    "closed_at": "Cerrado",
    # Toques / Campaigns
    "canal": "Canal",
    "enviados": "Enviados",
    "entregados": "Entregados",
    "clicks": "Clicks",
    "ctr": "CTR (%)",
    "tasa_entrega": "Tasa de Entrega (%)",
    "total_toques": "Total Toques",
    "total_clicks": "Total Clicks",
    # Derived
    "category": "Categoria",
    "periodo": "Periodo",
    "tipo_periodo": "Tipo Periodo",
    "entity": "Entidad",
    "tenant_id": "Proyecto",
    "cnt": "Cantidad",
}


def get_label(column_name: str) -> str:
    """Return a user-friendly Spanish label for a column name."""
    return COLUMN_LABELS.get(column_name, column_name.replace("_", " ").title())
