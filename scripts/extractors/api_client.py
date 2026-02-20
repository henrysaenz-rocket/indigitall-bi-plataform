"""HTTP client for the Indigitall API with JWT auth, retry, rate-limit, and logging."""

import time
from datetime import datetime, timezone

import requests
from sqlalchemy import text

from scripts.extractors.config import extraction_settings as cfg


class IndigitallAPIClient:
    """Manages authentication, retries, rate-limiting, and call logging."""

    def __init__(self, engine):
        self.engine = engine
        self.base_url = cfg.INDIGITALL_API_BASE_URL.rstrip("/")
        self.session = requests.Session()
        self.token: str | None = None

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def authenticate(self) -> str:
        """POST /v1/auth to obtain a JWT token."""
        url = f"{self.base_url}/v1/auth"
        payload = {"email": cfg.INDIGITALL_EMAIL, "password": cfg.INDIGITALL_PASSWORD}

        start = time.time()
        resp = self.session.post(url, json=payload, timeout=cfg.API_TIMEOUT_SECONDS)
        duration_ms = int((time.time() - start) * 1000)

        self._log_call(
            endpoint="/v1/auth",
            http_status=resp.status_code,
            duration_ms=duration_ms,
            error_message=None if resp.ok else resp.text[:500],
        )

        resp.raise_for_status()
        data = resp.json()

        # The token may come as data["token"] or data["accessToken"] — try both
        self.token = data.get("token") or data.get("accessToken") or data.get("jwt")
        if not self.token:
            raise ValueError(f"No token found in auth response. Keys: {list(data.keys())}")

        self.session.headers["Authorization"] = f"Bearer {self.token}"
        return self.token

    # ------------------------------------------------------------------
    # HTTP GET with retry / rate-limit
    # ------------------------------------------------------------------

    def get(self, endpoint: str, params: dict | None = None,
            application_id: str | None = None) -> dict | list | None:
        """GET with automatic retry on 401 (re-auth) and 429 (exponential backoff)."""
        url = f"{self.base_url}{endpoint}"

        for attempt in range(1, cfg.API_MAX_RETRIES + 1):
            # Rate-limit pause
            time.sleep(cfg.API_REQUEST_DELAY_SECONDS)

            start = time.time()
            try:
                resp = self.session.get(url, params=params, timeout=cfg.API_TIMEOUT_SECONDS)
            except requests.RequestException as exc:
                duration_ms = int((time.time() - start) * 1000)
                self._log_call(
                    endpoint=endpoint,
                    http_status=0,
                    duration_ms=duration_ms,
                    error_message=str(exc)[:500],
                    application_id=application_id,
                )
                if attempt == cfg.API_MAX_RETRIES:
                    raise
                time.sleep(2 ** attempt)
                continue

            duration_ms = int((time.time() - start) * 1000)

            # 401 → re-authenticate once then retry
            if resp.status_code == 401 and attempt == 1:
                self._log_call(
                    endpoint=endpoint,
                    http_status=401,
                    duration_ms=duration_ms,
                    error_message="Token expired — re-authenticating",
                    application_id=application_id,
                )
                self.authenticate()
                continue

            # 429 → exponential backoff
            if resp.status_code == 429:
                self._log_call(
                    endpoint=endpoint,
                    http_status=429,
                    duration_ms=duration_ms,
                    error_message="Rate limited — backing off",
                    application_id=application_id,
                )
                time.sleep(2 ** attempt)
                continue

            # Log and return
            self._log_call(
                endpoint=endpoint,
                http_status=resp.status_code,
                duration_ms=duration_ms,
                error_message=None if resp.ok else resp.text[:500],
                application_id=application_id,
            )

            if not resp.ok:
                print(f"    [WARN] {endpoint} returned {resp.status_code}")
                return None

            return resp.json()

        return None

    # ------------------------------------------------------------------
    # POST helper (some Indigitall stats endpoints use POST)
    # ------------------------------------------------------------------

    def post(self, endpoint: str, payload: dict | None = None,
             params: dict | None = None,
             application_id: str | None = None) -> dict | list | None:
        """POST with the same retry/logging logic as GET."""
        url = f"{self.base_url}{endpoint}"

        for attempt in range(1, cfg.API_MAX_RETRIES + 1):
            time.sleep(cfg.API_REQUEST_DELAY_SECONDS)

            start = time.time()
            try:
                resp = self.session.post(
                    url, json=payload, params=params,
                    timeout=cfg.API_TIMEOUT_SECONDS,
                )
            except requests.RequestException as exc:
                duration_ms = int((time.time() - start) * 1000)
                self._log_call(
                    endpoint=endpoint, http_status=0,
                    duration_ms=duration_ms,
                    error_message=str(exc)[:500],
                    application_id=application_id,
                )
                if attempt == cfg.API_MAX_RETRIES:
                    raise
                time.sleep(2 ** attempt)
                continue

            duration_ms = int((time.time() - start) * 1000)

            if resp.status_code == 401 and attempt == 1:
                self._log_call(
                    endpoint=endpoint, http_status=401,
                    duration_ms=duration_ms,
                    error_message="Token expired — re-authenticating",
                    application_id=application_id,
                )
                self.authenticate()
                continue

            if resp.status_code == 429:
                self._log_call(
                    endpoint=endpoint, http_status=429,
                    duration_ms=duration_ms,
                    error_message="Rate limited — backing off",
                    application_id=application_id,
                )
                time.sleep(2 ** attempt)
                continue

            self._log_call(
                endpoint=endpoint, http_status=resp.status_code,
                duration_ms=duration_ms,
                error_message=None if resp.ok else resp.text[:500],
                application_id=application_id,
            )

            if not resp.ok:
                print(f"    [WARN] {endpoint} returned {resp.status_code}")
                return None

            return resp.json()

        return None

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _log_call(self, endpoint: str, http_status: int, duration_ms: int,
                  error_message: str | None = None,
                  application_id: str | None = None):
        """Insert a row into raw.extraction_log."""
        now = datetime.now(timezone.utc)
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO raw.extraction_log
                            (application_id, endpoint, http_status, duration_ms,
                             error_message, started_at, finished_at)
                        VALUES
                            (:app_id, :endpoint, :status, :dur, :err, :started, :finished)
                    """),
                    {
                        "app_id": application_id,
                        "endpoint": endpoint,
                        "status": http_status,
                        "dur": duration_ms,
                        "err": error_message,
                        "started": now,
                        "finished": now,
                    },
                )
        except Exception as exc:
            print(f"    [WARN] Could not log API call: {exc}")
