"""Contacts / Agents extractor — 2 endpoints."""

from scripts.extractors.base_extractor import BaseExtractor
from scripts.extractors.config import extraction_settings as cfg


class ContactsExtractor(BaseExtractor):
    CHANNEL_NAME = "contacts"
    RAW_TABLE = "raw.raw_contacts_api"

    def _extract_for_app(self, app_id: str, app_meta: dict):
        endpoints = [
            {
                "name": "chat/contacts",
                "path": "/v1/chat/contacts",
                "params": {
                    "applicationId": app_id,
                    "page": 0,
                    "size": cfg.EXTRACTION_MAX_RECORDS,
                },
            },
            {
                "name": "chat/agents/status",
                "path": "/v1/chat/agents/status",
                "params": {"applicationId": app_id},
            },
        ]

        for ep in endpoints:
            try:
                data = self.client.get(ep["path"], params=ep["params"], application_id=app_id)
                self._store_raw(app_id, ep["path"], data)
                print(f"    {ep['name']}: OK")
            except Exception as exc:
                print(f"    {ep['name']}: FAILED ({exc})")
