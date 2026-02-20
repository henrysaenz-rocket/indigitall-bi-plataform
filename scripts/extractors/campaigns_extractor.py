"""Campaigns extractor — 1 endpoint."""

from scripts.extractors.base_extractor import BaseExtractor
from scripts.extractors.config import extraction_settings as cfg


class CampaignsExtractor(BaseExtractor):
    CHANNEL_NAME = "campaigns"
    RAW_TABLE = "raw.raw_campaigns_api"

    def _extract_for_app(self, app_id: str, app_meta: dict):
        endpoint = "/v1/campaign"
        params = {
            "applicationId": app_id,
            "page": 0,
            "size": cfg.EXTRACTION_MAX_RECORDS,
        }

        try:
            data = self.client.get(endpoint, params=params, application_id=app_id)
            self._store_raw(app_id, endpoint, data)
            print(f"    campaigns: OK")
        except Exception as exc:
            print(f"    campaigns: FAILED ({exc})")
