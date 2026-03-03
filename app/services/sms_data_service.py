"""SMS Data Service — Queries for sms_envios (250K+ records).

Available columns in sms_envios:
  id, tenant_id, sending_id, application_id, campaign_id,
  total_chunks, sending_type, is_flash, sent_at
"""

import pandas as pd
from datetime import date as date_type
from sqlalchemy import select, func, and_, text
from typing import Optional, Dict, Any, Tuple

from app.models.database import engine
from app.models.schemas import SmsEnvio


class SmsDataService:
    """Service for querying SMS sending data from sms_envios."""

    def _exec(self, stmt) -> pd.DataFrame:
        with engine.connect() as conn:
            return pd.read_sql(stmt, conn)

    def _base_where(self, t, start_date, end_date):
        w = True
        if start_date and end_date:
            w = and_(func.date(t.c.sent_at) >= start_date, func.date(t.c.sent_at) <= end_date)
        return w

    def get_sms_kpis(
        self,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
    ) -> Dict[str, Any]:
        """KPIs from actual sms_envios columns: enviados, chunks, campanas."""
        t = SmsEnvio.__table__
        w = self._base_where(t, start_date, end_date)

        stmt = select(
            func.count().label("total_enviados"),
            func.coalesce(func.sum(t.c.total_chunks), 0).label("total_chunks"),
            func.count(func.distinct(t.c.campaign_id)).label("campanas"),
            func.count(func.distinct(t.c.sending_type)).label("tipos_envio"),
        ).where(w)

        with engine.connect() as conn:
            row = conn.execute(stmt).first()

        total = row.total_enviados or 0
        return {
            "total_enviados": total,
            "total_chunks": row.total_chunks or 0,
            "campanas": row.campanas or 0,
            "tipos_envio": row.tipos_envio or 0,
            "total_clicks": 0,
            "ctr": 0,
            "delivered": 0,
            "delivery_rate": 0,
            "unique_phones": 0,
        }

    def get_sends_vs_chunks_trend(
        self,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
    ) -> pd.DataFrame:
        """Daily sends vs chunks."""
        t = SmsEnvio.__table__
        w = self._base_where(t, start_date, end_date)
        date_col = func.date(t.c.sent_at).label("date")
        stmt = (
            select(
                date_col,
                func.count().label("enviados"),
                func.coalesce(func.sum(t.c.total_chunks), 0).label("chunks"),
            )
            .where(w)
            .group_by(date_col)
            .order_by(date_col)
        )
        return self._exec(stmt)

    def get_sends_clicks_ctr_trend(
        self,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
    ) -> pd.DataFrame:
        """Daily sends and chunks trend (clicks not available in sms_envios)."""
        return self.get_sends_vs_chunks_trend(start_date, end_date)

    def get_campaign_ranking(
        self,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
        limit: int = 10,
    ) -> pd.DataFrame:
        """Top campaigns by volume (campaign_id only, name not available)."""
        t = SmsEnvio.__table__
        w = self._base_where(t, start_date, end_date)
        stmt = (
            select(
                t.c.campaign_id.label("campana_nombre"),
                func.count().label("total_enviados"),
                func.coalesce(func.sum(t.c.total_chunks), 0).label("chunks"),
            )
            .where(and_(w, t.c.campaign_id.isnot(None)))
            .group_by(t.c.campaign_id)
            .order_by(func.count().desc())
            .limit(limit)
        )
        df = self._exec(stmt)
        if not df.empty:
            df["campana_nombre"] = "Campana #" + df["campana_nombre"].astype(str)
        return df

    def get_campaign_ranking_by_ctr(
        self,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
        limit: int = 10,
    ) -> pd.DataFrame:
        """Top campaigns by volume (CTR not available, sorted by chunks/send)."""
        t = SmsEnvio.__table__
        w = self._base_where(t, start_date, end_date)
        stmt = (
            select(
                t.c.campaign_id.label("campana_nombre"),
                func.count().label("total_enviados"),
                func.coalesce(func.sum(t.c.total_chunks), 0).label("chunks"),
            )
            .where(and_(w, t.c.campaign_id.isnot(None)))
            .group_by(t.c.campaign_id)
            .having(func.count() > 100)
            .order_by(
                (func.coalesce(func.sum(t.c.total_chunks), 0) * 1.0 / func.count()).desc()
            )
            .limit(limit)
        )
        df = self._exec(stmt)
        if not df.empty:
            df["campana_nombre"] = "Campana #" + df["campana_nombre"].astype(str)
            df["chunks_per_send"] = (df["chunks"] / df["total_enviados"]).round(2)
        return df

    def get_heatmap_data(
        self,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
    ) -> pd.DataFrame:
        """Hour x Day-of-week heatmap."""
        t = SmsEnvio.__table__
        w = and_(self._base_where(t, start_date, end_date), t.c.sent_at.isnot(None))
        dow = func.to_char(t.c.sent_at, "Day").label("day_name")
        hour = func.extract("hour", t.c.sent_at).label("hora")
        dow_num = func.extract("isodow", t.c.sent_at).label("dow_num")
        stmt = (
            select(dow, hour, func.count().label("value"), dow_num)
            .where(w)
            .group_by(dow, hour, dow_num)
            .order_by(dow_num, hour)
        )
        df = self._exec(stmt)
        if not df.empty:
            day_map = {
                "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miercoles",
                "Thursday": "Jueves", "Friday": "Viernes",
                "Saturday": "Sabado", "Sunday": "Domingo",
            }
            df["dia_semana"] = df["day_name"].str.strip().map(lambda d: day_map.get(d, d))
            df = df[["dia_semana", "hora", "value"]]
        return df

    def get_sending_type_breakdown(
        self,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
    ) -> pd.DataFrame:
        """SMS counts by sending type."""
        t = SmsEnvio.__table__
        w = and_(self._base_where(t, start_date, end_date), t.c.sending_type.isnot(None))
        stmt = (
            select(t.c.sending_type, func.count().label("count"))
            .where(w)
            .group_by(t.c.sending_type)
            .order_by(func.count().desc())
        )
        return self._exec(stmt)

    def get_detail_page(
        self,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
        page: int = 0,
        page_size: int = 20,
    ) -> Tuple[pd.DataFrame, int]:
        """Paginated SMS detail table with total count."""
        t = SmsEnvio.__table__
        w = self._base_where(t, start_date, end_date)

        with engine.connect() as conn:
            total = conn.execute(select(func.count()).select_from(t).where(w)).scalar() or 0

        stmt = (
            select(
                func.date(t.c.sent_at).label("fecha"),
                t.c.campaign_id, t.c.sending_type,
                t.c.total_chunks, t.c.is_flash,
            )
            .where(w)
            .order_by(t.c.sent_at.desc())
            .offset(page * page_size)
            .limit(page_size)
        )
        return self._exec(stmt), total

    def get_drill_data(
        self,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
        granularity: str = "month",
    ) -> pd.DataFrame:
        """Aggregated SMS counts for drill-down (month/week/day)."""
        t = SmsEnvio.__table__
        w = self._base_where(t, start_date, end_date)

        if granularity == "month":
            period = func.to_char(t.c.sent_at, "YYYY-MM").label("period")
        elif granularity == "week":
            period = func.to_char(t.c.sent_at, "IYYY-\"W\"IW").label("period")
        else:
            period = func.date(t.c.sent_at).label("period")

        stmt = (
            select(
                period,
                func.count().label("total"),
                func.coalesce(func.sum(t.c.total_chunks), 0).label("chunks"),
            )
            .where(w)
            .group_by(period)
            .order_by(period)
        )
        return self._exec(stmt)
