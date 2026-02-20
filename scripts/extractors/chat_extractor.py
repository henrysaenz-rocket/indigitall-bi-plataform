"""Chat / WhatsApp extractor — 4 endpoints."""

from scripts.extractors.base_extractor import BaseExtractor


class ChatExtractor(BaseExtractor):
    CHANNEL_NAME = "chat"
    RAW_TABLE = "raw.raw_chat_stats"

    def _extract_for_app(self, app_id: str, app_meta: dict):
        endpoints = [
            {
                "name": "chat/stats",
                "path": f"/v1/application/{app_id}/chat/stats",
                "params": {"dateFrom": self.date_from_str, "dateTo": self.date_to_str},
            },
            {
                "name": "chat/stats/dates",
                "path": f"/v1/application/{app_id}/chat/stats/dates",
                "params": {"dateFrom": self.date_from_str, "dateTo": self.date_to_str},
            },
            {
                "name": "chat/agent/stats/dates",
                "path": f"/v1/application/{app_id}/chat/agent/stats/dates",
                "params": {"dateFrom": self.date_from_str, "dateTo": self.date_to_str},
            },
            {
                "name": "chat/summary",
                "path": f"/stats-service/chat/{app_id}/summary",
                "params": {"dateFrom": self.date_from_str, "dateTo": self.date_to_str},
            },
        ]

        for ep in endpoints:
            try:
                data = self.client.get(ep["path"], params=ep["params"], application_id=app_id)
                self._store_raw(app_id, ep["path"], data)
                print(f"    {ep['name']}: OK")
            except Exception as exc:
                print(f"    {ep['name']}: FAILED ({exc})")
