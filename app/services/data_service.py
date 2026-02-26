"""
Data Service — Conversations domain queries.
Migrated from Demo CSV reads → SQLAlchemy Core queries.
Returns pd.DataFrame to maintain API compatibility with ChartService.
"""

import pandas as pd
from datetime import date as date_type, timedelta
from sqlalchemy import select, func, text, case, and_
from typing import Optional, List, Dict, Any

from app.models.database import engine
from app.models.schemas import Message, Contact, Agent, DailyStat, SyncState


class DataService:
    """Service for querying conversation analytics data."""

    def _exec(self, stmt) -> pd.DataFrame:
        """Execute a SQLAlchemy statement and return a DataFrame."""
        with engine.connect() as conn:
            return pd.read_sql(stmt, conn)

    def _tenant_filter(self, table, tenant_id: Optional[str]):
        """Return a tenant WHERE clause, or True (no filter) if None."""
        if tenant_id:
            return table.c.tenant_id == tenant_id
        return True

    # --- Tenant list ---

    def get_entities(self) -> List[str]:
        """Get unique tenant IDs from contacts (or messages if available)."""
        # Try contacts first (populated by transform bridge)
        stmt = (
            select(Contact.tenant_id, func.count().label("cnt"))
            .group_by(Contact.tenant_id)
            .order_by(func.count().desc())
            .limit(50)
        )
        df = self._exec(stmt)
        if not df.empty:
            return df["tenant_id"].tolist()

        # Fallback to messages
        stmt = (
            select(Message.tenant_id, func.count().label("cnt"))
            .group_by(Message.tenant_id)
            .order_by(func.count().desc())
            .limit(50)
        )
        df = self._exec(stmt)
        return df["tenant_id"].tolist() if not df.empty else []

    # --- Summary stats ---

    def get_summary_stats(self, tenant_filter: Optional[str] = None) -> Dict[str, Any]:
        """Aggregate KPIs from multiple tables.

        Uses messages table if populated, otherwise falls back to
        contacts + daily_stats + raw agent count from chat_stats.
        """
        with engine.connect() as conn:
            # Check if messages table has data for this tenant
            t = Message.__table__
            w = self._tenant_filter(t, tenant_filter)
            msg_count = conn.execute(
                select(func.count()).select_from(t).where(w)
            ).scalar() or 0

            if msg_count > 0:
                # Original path: derive everything from messages
                row = conn.execute(
                    select(
                        func.count().label("total_messages"),
                        func.count(func.distinct(t.c.contact_id)).label("unique_contacts"),
                        func.count(func.distinct(t.c.agent_id)).label("active_agents"),
                        func.count(func.distinct(t.c.conversation_id)).label("total_conversations"),
                    ).where(w)
                ).first()
                return {
                    "total_messages": row.total_messages or 0,
                    "unique_contacts": row.unique_contacts or 0,
                    "active_agents": row.active_agents or 0,
                    "total_conversations": row.total_conversations or 0,
                }

            # Fallback: aggregate from contacts, daily_stats, and raw chat_stats
            ct = Contact.__table__
            cw = self._tenant_filter(ct, tenant_filter)
            unique_contacts = conn.execute(
                select(func.count()).select_from(ct).where(cw)
            ).scalar() or 0

            dt = DailyStat.__table__
            dw = self._tenant_filter(dt, tenant_filter)
            row = conn.execute(
                select(
                    func.coalesce(func.sum(dt.c.total_messages), 0).label("total_messages"),
                    func.coalesce(func.sum(dt.c.conversations), 0).label("conversations"),
                ).where(dw)
            ).first()
            total_messages = row.total_messages or 0
            total_conversations = row.conversations or 0

            # Active agents from raw.raw_chat_stats (latest snapshot)
            active_agents = 0
            try:
                agent_row = conn.execute(text("""
                    SELECT (source_data->'data'->>'activeAgents')::int
                    FROM raw.raw_chat_stats
                    WHERE endpoint LIKE '%/agent/status%'
                    ORDER BY loaded_at DESC LIMIT 1
                """)).first()
                if agent_row:
                    active_agents = agent_row[0] or 0
            except Exception:
                pass

            return {
                "total_messages": total_messages,
                "unique_contacts": unique_contacts,
                "active_agents": active_agents,
                "total_conversations": total_conversations,
            }

    # --- Recent messages ---

    def get_recent_messages(self, tenant_filter: Optional[str] = None, limit: int = 10) -> pd.DataFrame:
        t = Message.__table__
        stmt = (
            select(t)
            .where(self._tenant_filter(t, tenant_filter))
            .order_by(t.c.timestamp.desc())
            .limit(limit)
        )
        return self._exec(stmt)

    # --- Grouping queries ---

    def get_messages_by_direction(self, tenant_filter: Optional[str] = None) -> pd.DataFrame:
        t = Message.__table__
        stmt = (
            select(t.c.direction, func.count().label("count"))
            .where(self._tenant_filter(t, tenant_filter))
            .group_by(t.c.direction)
        )
        return self._exec(stmt)

    def get_messages_by_hour(self, tenant_filter: Optional[str] = None) -> pd.DataFrame:
        t = Message.__table__
        stmt = (
            select(t.c.hour, func.count().label("count"))
            .where(self._tenant_filter(t, tenant_filter))
            .group_by(t.c.hour)
            .order_by(t.c.hour)
        )
        return self._exec(stmt)

    def get_messages_over_time(self, tenant_filter: Optional[str] = None) -> pd.DataFrame:
        t = Message.__table__
        stmt = (
            select(t.c.date, func.count().label("count"))
            .where(self._tenant_filter(t, tenant_filter))
            .group_by(t.c.date)
            .order_by(t.c.date)
        )
        return self._exec(stmt)

    def get_messages_by_day_of_week(self, tenant_filter: Optional[str] = None) -> pd.DataFrame:
        t = Message.__table__
        day_order = case(
            (t.c.day_of_week == "Monday", 1),
            (t.c.day_of_week == "Tuesday", 2),
            (t.c.day_of_week == "Wednesday", 3),
            (t.c.day_of_week == "Thursday", 4),
            (t.c.day_of_week == "Friday", 5),
            (t.c.day_of_week == "Saturday", 6),
            (t.c.day_of_week == "Sunday", 7),
            else_=8,
        )
        stmt = (
            select(t.c.day_of_week, func.count().label("count"))
            .where(self._tenant_filter(t, tenant_filter))
            .group_by(t.c.day_of_week)
            .order_by(day_order)
        )
        return self._exec(stmt)

    # --- Top-N queries ---

    def get_top_contacts(self, tenant_filter: Optional[str] = None, limit: int = 10) -> pd.DataFrame:
        t = Message.__table__
        stmt = (
            select(t.c.contact_name, func.count().label("message_count"))
            .where(self._tenant_filter(t, tenant_filter))
            .group_by(t.c.contact_name)
            .order_by(func.count().desc())
            .limit(limit)
        )
        return self._exec(stmt)

    def get_intent_distribution(self, tenant_filter: Optional[str] = None, limit: int = 10) -> pd.DataFrame:
        t = Message.__table__
        stmt = (
            select(t.c.intent, func.count().label("count"))
            .where(and_(self._tenant_filter(t, tenant_filter), t.c.intent.isnot(None)))
            .group_by(t.c.intent)
            .order_by(func.count().desc())
            .limit(limit)
        )
        return self._exec(stmt)

    def get_agent_performance(self, tenant_filter: Optional[str] = None) -> pd.DataFrame:
        t = Message.__table__
        stmt = (
            select(
                t.c.agent_id,
                func.count().label("messages"),
                func.count(func.distinct(t.c.conversation_id)).label("conversations"),
            )
            .where(and_(self._tenant_filter(t, tenant_filter), t.c.agent_id.isnot(None)))
            .group_by(t.c.agent_id)
            .order_by(func.count().desc())
        )
        return self._exec(stmt)

    # --- Fallback rate ---

    def get_fallback_rate(self, tenant_filter: Optional[str] = None) -> Dict[str, Any]:
        t = Message.__table__
        w = self._tenant_filter(t, tenant_filter)
        stmt = select(
            func.count().label("total"),
            func.count().filter(t.c.is_fallback == True).label("fallback_count"),  # noqa: E712
        ).where(w)

        with engine.connect() as conn:
            row = conn.execute(stmt).first()

        total = row.total or 0
        fb = row.fallback_count or 0
        return {
            "fallback_count": fb,
            "total": total,
            "rate": round(fb / total * 100, 2) if total > 0 else 0,
        }

    # --- High-message customers ---

    def get_customers_with_high_messages(
        self,
        period: str = "day",
        threshold: int = 4,
        tenant_filter: Optional[str] = None,
    ) -> pd.DataFrame:
        t = Message.__table__

        if period == "week":
            period_expr = func.to_char(t.c.date, "IYYY-\"W\"IW")
            period_label = "Semana"
        elif period == "month":
            period_expr = func.to_char(t.c.date, "YYYY-MM")
            period_label = "Mes"
        else:
            period_expr = func.to_char(t.c.date, "YYYY-MM-DD")
            period_label = "Dia"

        stmt = (
            select(
                t.c.contact_id,
                t.c.contact_name,
                t.c.tenant_id.label("entity"),
                period_expr.label("periodo"),
                func.count().label("message_count"),
            )
            .where(self._tenant_filter(t, tenant_filter))
            .group_by(t.c.contact_id, t.c.contact_name, t.c.tenant_id, period_expr)
            .having(func.count() > threshold)
            .order_by(period_expr.desc(), func.count().desc())
        )
        df = self._exec(stmt)
        if not df.empty:
            df["tipo_periodo"] = period_label
        return df

    # --- Utility ---

    def get_date_range(self) -> Dict[str, Any]:
        t = Message.__table__
        stmt = select(func.min(t.c.date).label("min_date"), func.max(t.c.date).label("max_date"))
        with engine.connect() as conn:
            row = conn.execute(stmt).first()
        return {"min_date": row.min_date, "max_date": row.max_date}

    def get_messages_dataframe(self, tenant_filter: Optional[str] = None) -> pd.DataFrame:
        t = Message.__table__
        stmt = select(t).where(self._tenant_filter(t, tenant_filter))
        return self._exec(stmt)

    # --- Operations dashboard: filtered queries ---

    def get_summary_stats_for_period(
        self,
        tenant_filter: Optional[str] = None,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
    ) -> Dict[str, Any]:
        """KPIs for a date range with trend vs. the immediately preceding period."""
        with engine.connect() as conn:
            t = Message.__table__
            w = self._tenant_filter(t, tenant_filter)
            msg_count = conn.execute(
                select(func.count()).select_from(t).where(w)
            ).scalar() or 0

            use_messages = msg_count > 0
            if use_messages and start_date and end_date:
                cur = self._period_kpis_messages(conn, t, w, start_date, end_date)
                delta = (end_date - start_date).days + 1
                prev_end = start_date - timedelta(days=1)
                prev_start = prev_end - timedelta(days=delta - 1)
                prev = self._period_kpis_messages(conn, t, w, prev_start, prev_end)
            else:
                cur = self._period_kpis_daily(conn, tenant_filter, start_date, end_date)
                if start_date and end_date:
                    delta = (end_date - start_date).days + 1
                    prev_end = start_date - timedelta(days=1)
                    prev_start = prev_end - timedelta(days=delta - 1)
                else:
                    prev_start = prev_end = None
                prev = self._period_kpis_daily(conn, tenant_filter, prev_start, prev_end)

        for k, v in prev.items():
            cur[f"prev_{k}"] = v
        return cur

    @staticmethod
    def _period_kpis_messages(conn, t, base_where, start, end):
        f = and_(base_where, t.c.date >= start, t.c.date <= end)
        row = conn.execute(
            select(
                func.count().label("total_messages"),
                func.count(func.distinct(t.c.contact_id)).label("unique_contacts"),
                func.count(func.distinct(t.c.conversation_id)).label("conversations"),
                func.sum(case((t.c.is_fallback == True, 1), else_=0)).label("fallback_count"),  # noqa: E712
                func.avg(t.c.wait_time_seconds).label("avg_wait_seconds"),
            ).where(f)
        ).first()
        total = row.total_messages or 0
        fb = row.fallback_count or 0
        return {
            "total_messages": total,
            "unique_contacts": row.unique_contacts or 0,
            "conversations": row.conversations or 0,
            "avg_wait_seconds": round(float(row.avg_wait_seconds or 0), 1),
            "fallback_rate": round(fb / total * 100, 2) if total > 0 else 0,
        }

    def _period_kpis_daily(self, conn, tenant_filter, start, end):
        dt = DailyStat.__table__
        dw = self._tenant_filter(dt, tenant_filter)
        if start and end:
            dw = and_(dw, dt.c.date >= start, dt.c.date <= end)
        row = conn.execute(
            select(
                func.coalesce(func.sum(dt.c.total_messages), 0).label("total_messages"),
                func.coalesce(func.sum(dt.c.unique_contacts), 0).label("unique_contacts"),
                func.coalesce(func.sum(dt.c.conversations), 0).label("conversations"),
                func.coalesce(func.sum(dt.c.fallback_count), 0).label("fallback_count"),
            ).where(dw)
        ).first()
        total = row.total_messages or 0
        fb = row.fallback_count or 0
        return {
            "total_messages": total,
            "unique_contacts": row.unique_contacts or 0,
            "conversations": row.conversations or 0,
            "avg_wait_seconds": 0,
            "fallback_rate": round(fb / total * 100, 2) if total > 0 else 0,
        }

    def get_messages_over_time_filtered(
        self,
        tenant_filter: Optional[str] = None,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
    ) -> pd.DataFrame:
        """Messages per day within a date range (falls back to DailyStat)."""
        t = Message.__table__
        w = self._tenant_filter(t, tenant_filter)
        if start_date and end_date:
            w = and_(w, t.c.date >= start_date, t.c.date <= end_date)
        stmt = (
            select(t.c.date, func.count().label("count"))
            .where(w)
            .group_by(t.c.date)
            .order_by(t.c.date)
        )
        df = self._exec(stmt)
        if df.empty and start_date and end_date:
            dt = DailyStat.__table__
            dw = self._tenant_filter(dt, tenant_filter)
            dw = and_(dw, dt.c.date >= start_date, dt.c.date <= end_date)
            stmt = (
                select(dt.c.date, dt.c.total_messages.label("count"))
                .where(dw)
                .order_by(dt.c.date)
            )
            df = self._exec(stmt)
        return df

    def get_direction_breakdown_filtered(
        self,
        tenant_filter: Optional[str] = None,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
    ) -> pd.DataFrame:
        """Messages by direction within a date range."""
        t = Message.__table__
        w = self._tenant_filter(t, tenant_filter)
        if start_date and end_date:
            w = and_(w, t.c.date >= start_date, t.c.date <= end_date)
        stmt = (
            select(t.c.direction, func.count().label("count"))
            .where(w)
            .group_by(t.c.direction)
        )
        return self._exec(stmt)

    def get_agent_performance_detailed(
        self, tenant_filter: Optional[str] = None,
    ) -> pd.DataFrame:
        """Agent-level metrics (tries dbt mart, then messages, then agents table)."""
        # Try dbt mart first
        try:
            sql = text(
                "SELECT agent_id, total_messages, conversations_handled, "
                "unique_contacts, avg_handle_seconds, avg_wait_seconds, active_days "
                "FROM marts.fct_agent_performance WHERE tenant_id = :tenant"
            )
            with engine.connect() as conn:
                df = pd.read_sql(sql, conn, params={"tenant": tenant_filter})
            if not df.empty:
                return df
        except Exception:
            pass

        # Fallback: aggregate from messages
        t = Message.__table__
        w = and_(self._tenant_filter(t, tenant_filter), t.c.agent_id.isnot(None))
        stmt = (
            select(
                t.c.agent_id,
                func.count().label("total_messages"),
                func.count(func.distinct(t.c.conversation_id)).label("conversations_handled"),
                func.count(func.distinct(t.c.contact_id)).label("unique_contacts"),
                func.avg(t.c.handle_time_seconds).label("avg_handle_seconds"),
                func.avg(t.c.wait_time_seconds).label("avg_wait_seconds"),
                func.count(func.distinct(t.c.date)).label("active_days"),
            )
            .where(w)
            .group_by(t.c.agent_id)
            .order_by(func.count().desc())
        )
        df = self._exec(stmt)
        if not df.empty:
            return df

        # Final fallback: agents table
        at = Agent.__table__
        aw = self._tenant_filter(at, tenant_filter)
        stmt = (
            select(
                at.c.agent_id,
                at.c.total_messages,
                at.c.conversations_handled,
            )
            .where(aw)
            .order_by(at.c.total_messages.desc())
        )
        df = self._exec(stmt)
        for col in ["unique_contacts", "avg_handle_seconds", "avg_wait_seconds", "active_days"]:
            if col not in df.columns:
                df[col] = 0
        return df

    def get_contacts_dataframe(self, tenant_filter: Optional[str] = None) -> pd.DataFrame:
        t = Contact.__table__
        stmt = select(t).where(self._tenant_filter(t, tenant_filter))
        return self._exec(stmt)

    def get_schema_description(self) -> str:
        """Schema description for the AI agent system prompt."""
        return """
=== CONTEXTO DE NEGOCIO ===

Esta plataforma analiza datos de WhatsApp Business para la Red Coopcentral, una red de cooperativas financieras en Colombia.

TABLA PRINCIPAL: messages
Columnas: message_id, timestamp, date, hour, day_of_week, send_type, direction, content_type, status, contact_name, contact_id, tenant_id, conversation_id, agent_id, close_reason, intent, is_fallback, message_body, is_bot, is_human, wait_time_seconds, handle_time_seconds

TIPOS DE MENSAJE (direction): Inbound, Bot, Agent, Outbound, System
INDICADOR DE FALLBACK (is_fallback): true/false

contacts: contact_id, contact_name, tenant_id, total_messages, first_contact, last_contact, total_conversations
agents: agent_id, total_messages, conversations_handled, avg_handle_time_seconds

METRICAS CLAVE:
1. Tasa de Fallback: COUNT(is_fallback=true) / COUNT(*) * 100 — Meta: < 15%
2. Volumen de mensajes y tendencia diaria
3. Distribucion por canal (Inbound vs Bot vs Agent)
4. Tiempo de espera (wait_time_seconds) — Meta: < 60s
5. Tiempo de atencion (handle_time_seconds) — Meta: < 300s
"""
