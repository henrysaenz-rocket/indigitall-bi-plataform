"""Push notifications extractor — 4 endpoints."""

from scripts.extractors.base_extractor import BaseExtractor


class PushExtractor(BaseExtractor):
    CHANNEL_NAME = "push"
    RAW_TABLE = "raw.raw_push_stats"

    def _extract_for_app(self, app_id: str, app_meta: dict):
        endpoints = [
            {
                "name": "stats",
                "path": f"/v1/application/{app_id}/stats",
                "params": {"dateFrom": self.date_from_str, "dateTo": self.date_to_str},
            },
            {
                "name": "stats/dates",
                "path": f"/v1/application/{app_id}/stats/dates",
                "params": {"dateFrom": self.date_from_str, "dateTo": self.date_to_str},
            },
            {
                "name": "stats/devices",
                "path": f"/v1/application/{app_id}/stats/devices",
                "params": {"dateFrom": self.date_from_str, "dateTo": self.date_to_str},
            },
            {
                "name": "heatmap",
                "path": f"/v1/application/{app_id}/heatmap",
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
