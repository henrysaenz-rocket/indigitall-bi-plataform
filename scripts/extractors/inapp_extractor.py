"""In-App / Web extractor — 2 endpoints."""

from scripts.extractors.base_extractor import BaseExtractor


class InAppExtractor(BaseExtractor):
    CHANNEL_NAME = "inapp"
    RAW_TABLE = "raw.raw_inapp_stats"

    def _extract_for_app(self, app_id: str, app_meta: dict):
        endpoints = [
            {
                "name": "inapp/stats/application",
                "path": "/inapp/stats/application",
                "params": {
                    "applicationId": app_id,
                    "dateFrom": self.date_from_str,
                    "dateTo": self.date_to_str,
                },
            },
            {
                "name": "inapp/stats/campaign",
                "path": "/inapp/stats/campaign",
                "params": {
                    "applicationId": app_id,
                    "dateFrom": self.date_from_str,
                    "dateTo": self.date_to_str,
                },
            },
        ]

        for ep in endpoints:
            try:
                data = self.client.get(ep["path"], params=ep["params"], application_id=app_id)
                self._store_raw(app_id, ep["path"], data)
                print(f"    {ep['name']}: OK")
            except Exception as exc:
                print(f"    {ep['name']}: FAILED ({exc})")
