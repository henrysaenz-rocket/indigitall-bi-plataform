"""Contact Center Service — Queries for agent conversation analytics."""

import pandas as pd
from datetime import date as date_type
from sqlalchemy import select, func, and_, case
from typing import Optional, Dict, Any

from app.models.database import engine
from app.models.schemas import ChatConversation


class ContactCenterService:
    """Service for querying contact center / chat conversation data."""

    def _exec(self, stmt) -> pd.DataFrame:
        with engine.connect() as conn:
            return pd.read_sql(stmt, conn)

    def _tenant_filter(self, table, tenant_id: Optional[str]):
        if tenant_id:
            return table.c.tenant_id == tenant_id
        return True

    def _base_where(self, t, tenant, start_date, end_date):
        w = self._tenant_filter(t, tenant)
        if start_date and end_date:
            w = and_(w, func.date(t.c.closed_at) >= start_date, func.date(t.c.closed_at) <= end_date)
        return w

    def get_cc_kpis(
        self,
        tenant_filter: Optional[str] = None,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
    ) -> Dict[str, Any]:
        """Contact center KPIs: total convs, active agents, avg wait, avg handle."""
        t = ChatConversation.__table__
        w = self._base_where(t, tenant_filter, start_date, end_date)

        stmt = select(
            func.count().label("total_conversations"),
            func.count(func.distinct(t.c.agent_id)).label("active_agents"),
            func.avg(t.c.wait_time_seconds).label("avg_wait"),
            func.avg(t.c.handle_time_seconds).label("avg_handle"),
        ).where(w)

        with engine.connect() as conn:
            row = conn.execute(stmt).first()

        return {
            "total_conversations": row.total_conversations or 0,
            "active_agents": row.active_agents or 0,
            "avg_wait_minutes": round(float(row.avg_wait or 0) / 60, 1),
            "avg_handle_minutes": round(float(row.avg_handle or 0) / 60, 1),
        }

    def get_conversations_over_time(
        self,
        tenant_filter: Optional[str] = None,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
    ) -> pd.DataFrame:
        """Daily conversation count."""
        t = ChatConversation.__table__
        w = self._base_where(t, tenant_filter, start_date, end_date)
        date_col = func.date(t.c.closed_at).label("date")
        stmt = (
            select(date_col, func.count().label("count"))
            .where(w)
            .group_by(date_col)
            .order_by(date_col)
        )
        return self._exec(stmt)

    def get_conversations_by_agent(
        self,
        tenant_filter: Optional[str] = None,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
        limit: int = 15,
    ) -> pd.DataFrame:
        """Conversation count per agent."""
        t = ChatConversation.__table__
        w = and_(self._base_where(t, tenant_filter, start_date, end_date), t.c.agent_id.isnot(None))
        stmt = (
            select(
                t.c.agent_id,
                func.count().label("conversations"),
                func.count(func.distinct(t.c.contact_id)).label("contacts"),
            )
            .where(w)
            .group_by(t.c.agent_id)
            .order_by(func.count().desc())
            .limit(limit)
        )
        return self._exec(stmt)

    def get_close_reasons(
        self,
        tenant_filter: Optional[str] = None,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
    ) -> pd.DataFrame:
        """Conversation count by close reason (derived from messages)."""
        from app.models.schemas import Message
        t = Message.__table__
        w = self._tenant_filter(t, tenant_filter)
        if start_date and end_date:
            w = and_(w, t.c.date >= start_date, t.c.date <= end_date)
        w = and_(w, t.c.close_reason.isnot(None), t.c.close_reason != "")
        stmt = (
            select(t.c.close_reason.label("reason"), func.count().label("count"))
            .where(w)
            .group_by(t.c.close_reason)
            .order_by(func.count().desc())
        )
        return self._exec(stmt)

    def get_wait_time_distribution(
        self,
        tenant_filter: Optional[str] = None,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
    ) -> pd.DataFrame:
        """Wait time in buckets (0-1m, 1-5m, 5-15m, 15-30m, 30m+)."""
        t = ChatConversation.__table__
        w = and_(
            self._base_where(t, tenant_filter, start_date, end_date),
            t.c.wait_time_seconds.isnot(None),
        )
        bucket = case(
            (t.c.wait_time_seconds < 60, "0-1 min"),
            (t.c.wait_time_seconds < 300, "1-5 min"),
            (t.c.wait_time_seconds < 900, "5-15 min"),
            (t.c.wait_time_seconds < 1800, "15-30 min"),
            else_="30+ min",
        )
        stmt = (
            select(bucket.label("bucket"), func.count().label("count"))
            .where(w)
            .group_by(bucket)
        )
        df = self._exec(stmt)
        if not df.empty:
            order = ["0-1 min", "1-5 min", "5-15 min", "15-30 min", "30+ min"]
            df["bucket"] = pd.Categorical(df["bucket"], categories=order, ordered=True)
            df = df.sort_values("bucket").reset_index(drop=True)
        return df

    def get_hourly_queue(
        self,
        tenant_filter: Optional[str] = None,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
    ) -> pd.DataFrame:
        """Conversations by hour of day (queued_at)."""
        t = ChatConversation.__table__
        w = and_(
            self._base_where(t, tenant_filter, start_date, end_date),
            t.c.queued_at.isnot(None),
        )
        hour_col = func.extract("hour", t.c.queued_at).label("hour")
        stmt = (
            select(hour_col, func.count().label("count"))
            .where(w)
            .group_by(hour_col)
            .order_by(hour_col)
        )
        return self._exec(stmt)
