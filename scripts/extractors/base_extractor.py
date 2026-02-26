"""Base extractor — common logic for all channel extractors."""

import json
from abc import ABC, abstractmethod
from datetime import date, timedelta

from sqlalchemy import text

from scripts.extractors.config import extraction_settings as cfg
from scripts.extractors.api_client import IndigitallAPIClient

TENANT_ID = "visionamos"


class BaseExtractor(ABC):
    """Abstract base class for channel-specific extractors."""

    CHANNEL_NAME: str = "base"
    RAW_TABLE: str = "raw.raw_applications"  # override in subclass

    def __init__(self, client: IndigitallAPIClient, engine,
                 full_refresh: bool = False):
        self.client = client
        self.engine = engine
        self.full_refresh = full_refresh
        self.date_to = date.today()
        self.date_from = self.date_to - timedelta(days=cfg.EXTRACTION_DAYS_BACK)
        self.records_stored = 0

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def extract(self, applications: list[dict]) -> int:
        """Run extraction for all given applications. Returns total records stored."""
        self.records_stored = 0
        for app in applications:
            app_id = app.get("id") or app.get("appKey") or app.get("applicationId", "unknown")
            app_name = app.get("name", "unknown")
            print(f"  [{self.CHANNEL_NAME}] App {app_name} ({app_id})")
            try:
                self._extract_for_app(str(app_id), app)
            except Exception as exc:
                print(f"    [ERROR] {self.CHANNEL_NAME} failed for {app_id}: {exc}")
        return self.records_stored

    # ------------------------------------------------------------------
    # Abstract
    # ------------------------------------------------------------------

    @abstractmethod
    def _extract_for_app(self, app_id: str, app_meta: dict):
        """Subclass implements channel-specific API calls here."""
        ...

    # ------------------------------------------------------------------
    # Storage helper
    # ------------------------------------------------------------------

    def _store_raw(self, app_id: str, endpoint: str, data,
                   tenant_id: str | None = None):
        """Insert one JSONB row into the channel's raw table."""
        if data is None:
            return
        with self.engine.begin() as conn:
            conn.execute(
                text(f"""
                    INSERT INTO {self.RAW_TABLE}
                        (application_id, tenant_id, endpoint, date_from, date_to, source_data)
                    VALUES
                        (:app_id, :tenant, :endpoint, :dfrom, :dto, :data)
                """),
                {
                    "app_id": app_id,
                    "tenant": tenant_id,
                    "endpoint": endpoint,
                    "dfrom": self.date_from,
                    "dto": self.date_to,
                    "data": json.dumps(data) if not isinstance(data, str) else data,
                },
            )
        self.records_stored += 1

    # ------------------------------------------------------------------
    # Cursor helpers (incremental extraction)
    # ------------------------------------------------------------------

    def _get_cursor(self, entity: str) -> str | None:
        """Read last_cursor from sync_state for incremental extraction."""
        if self.full_refresh:
            return None
        with self.engine.connect() as conn:
            row = conn.execute(
                text("""
                    SELECT last_cursor FROM public.sync_state
                    WHERE tenant_id = :tid AND entity = :entity
                """),
                {"tid": TENANT_ID, "entity": entity},
            ).fetchone()
            return row[0] if row else None

    def _update_cursor(self, entity: str, cursor_value: str):
        """Write last_cursor to sync_state for the given entity."""
        with self.engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO public.sync_state (tenant_id, entity, last_cursor, status)
                    VALUES (:tid, :entity, :cursor, 'success')
                    ON CONFLICT (tenant_id, entity) DO UPDATE SET
                        last_cursor = EXCLUDED.last_cursor
                """),
                {"tid": TENANT_ID, "entity": entity, "cursor": cursor_value},
            )

    # ------------------------------------------------------------------
    # Date helpers (formatted for Indigitall API)
    # ------------------------------------------------------------------

    @property
    def date_from_str(self) -> str:
        return self.date_from.isoformat()

    @property
    def date_to_str(self) -> str:
        return self.date_to.isoformat()
