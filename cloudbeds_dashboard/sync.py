from __future__ import annotations

import threading
import time
from datetime import datetime, timezone


class SyncState:
    def __init__(self) -> None:
        self.last_reconciliation_at: str | None = None
        self.last_webhook_at: str | None = None


STATE = SyncState()


class CloudbedsClient:
    """Stub for Cloudbeds API integration.

    Replace this with real authentication and API calls to fetch reservations
    for the next 14-30 days and feed into upsert logic.
    """

    def fetch_reservations(self) -> list[dict]:
        return []


def record_webhook_received() -> None:
    STATE.last_webhook_at = datetime.now(timezone.utc).isoformat()


def start_reconciliation_loop(interval_seconds: int = 1800) -> None:
    def run() -> None:
        client = CloudbedsClient()
        while True:
            _ = client.fetch_reservations()
            STATE.last_reconciliation_at = datetime.now(timezone.utc).isoformat()
            time.sleep(interval_seconds)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
