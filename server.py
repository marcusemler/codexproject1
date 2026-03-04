from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from cloudbeds_dashboard.db import init_db
from cloudbeds_dashboard.service import get_cancelled, get_upcoming, upsert_reservation
from cloudbeds_dashboard.sync import STATE, record_webhook_received, start_reconciliation_loop

STATIC_DIR = Path(__file__).parent / "static"


class AppHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str) -> None:
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            return self._send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
        if parsed.path == "/static/app.js":
            return self._send_file(STATIC_DIR / "app.js", "application/javascript; charset=utf-8")
        if parsed.path == "/static/styles.css":
            return self._send_file(STATIC_DIR / "styles.css", "text/css; charset=utf-8")
        if parsed.path == "/api/packages/upcoming":
            q = parse_qs(parsed.query)
            days = int(q.get("days", ["14"])[0])
            prop = q.get("property", ["all"])[0]
            try:
                data = get_upcoming(days=days, property_filter=prop)
            except ValueError as exc:
                return self._send_json(400, {"error": str(exc)})
            return self._send_json(200, {"items": data})
        if parsed.path == "/api/packages/cancelled":
            q = parse_qs(parsed.query)
            days = int(q.get("days", ["14"])[0])
            prop = q.get("property", ["all"])[0]
            try:
                data = get_cancelled(days=days, property_filter=prop)
            except ValueError as exc:
                return self._send_json(400, {"error": str(exc)})
            return self._send_json(200, {"items": data})
        if parsed.path == "/health":
            return self._send_json(
                200,
                {
                    "ok": True,
                    "last_webhook_at": STATE.last_webhook_at,
                    "last_reconciliation_at": STATE.last_reconciliation_at,
                },
            )

        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/webhooks/cloudbeds":
            self.send_error(404)
            return

        content_len = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_len)
        try:
            payload = json.loads(raw)
            upsert_reservation(payload)
            record_webhook_received()
        except (json.JSONDecodeError, ValueError) as exc:
            return self._send_json(400, {"error": str(exc)})

        return self._send_json(202, {"accepted": True})


def seed_demo_data() -> None:
    samples = [
        {
            "reservation_id": "CB-1001",
            "property_id": "encore",
            "property_name": "Berlin Encore",
            "guest_name": "Alex Rivera",
            "arrival_date": "2026-03-08",
            "departure_date": "2026-03-10",
            "package_name": "Spa Weekend",
            "package_code": "SPA-01",
            "status": "booked",
            "source_updated_at": "2026-03-01T08:00:00Z",
        },
        {
            "reservation_id": "CB-1002",
            "property_id": "resort",
            "property_name": "Berlin Resort",
            "guest_name": "Sam Patel",
            "arrival_date": "2026-03-12",
            "departure_date": "2026-03-15",
            "package_name": "Family Escape",
            "package_code": "FAM-02",
            "status": "cancelled",
            "source_updated_at": "2026-03-02T11:30:00Z",
        },
    ]
    for row in samples:
        try:
            upsert_reservation(row)
        except ValueError:
            pass


if __name__ == "__main__":
    init_db()
    seed_demo_data()
    start_reconciliation_loop()
    server = ThreadingHTTPServer(("0.0.0.0", 8000), AppHandler)
    print("Dashboard running on http://localhost:8000")
    server.serve_forever()
