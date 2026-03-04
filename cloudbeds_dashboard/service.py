from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from cloudbeds_dashboard.db import get_connection


ALLOWED_PROPERTIES = {"all", "encore", "resort"}


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_property_name(property_id: str, property_name: str | None) -> str:
    if property_name:
        return property_name
    return "Berlin Encore" if property_id == "encore" else "Berlin Resort"


def upsert_reservation(payload: dict[str, Any]) -> None:
    required = ["reservation_id", "property_id", "arrival_date", "status"]
    missing = [k for k in required if not payload.get(k)]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")

    status = payload["status"].lower()
    if status not in {"booked", "modified", "cancelled"}:
        raise ValueError("status must be one of booked|modified|cancelled")

    property_id = payload["property_id"].lower()
    if property_id not in {"encore", "resort"}:
        raise ValueError("property_id must be one of encore|resort")

    cancelled_at = now_utc_iso() if status == "cancelled" else None

    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO reservations (
                reservation_id, property_id, property_name, guest_name,
                arrival_date, departure_date, package_name, package_code,
                status, cancelled_at, source_updated_at, last_seen_at, raw_payload
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(reservation_id, property_id) DO UPDATE SET
                property_name=excluded.property_name,
                guest_name=excluded.guest_name,
                arrival_date=excluded.arrival_date,
                departure_date=excluded.departure_date,
                package_name=excluded.package_name,
                package_code=excluded.package_code,
                status=excluded.status,
                cancelled_at=excluded.cancelled_at,
                source_updated_at=excluded.source_updated_at,
                last_seen_at=excluded.last_seen_at,
                raw_payload=excluded.raw_payload
            """,
            (
                payload["reservation_id"],
                property_id,
                normalize_property_name(property_id, payload.get("property_name")),
                payload.get("guest_name"),
                payload["arrival_date"],
                payload.get("departure_date"),
                payload.get("package_name"),
                payload.get("package_code"),
                status,
                cancelled_at,
                payload.get("source_updated_at"),
                now_utc_iso(),
                json.dumps(payload),
            ),
        )


def _window_dates(days: int) -> tuple[str, str]:
    start = datetime.now(timezone.utc).date()
    end = start + timedelta(days=days)
    return start.isoformat(), end.isoformat()


def _property_clause(property_filter: str) -> tuple[str, list[Any]]:
    if property_filter not in ALLOWED_PROPERTIES:
        raise ValueError("property must be one of all|encore|resort")
    if property_filter == "all":
        return "", []
    return " AND property_id = ?", [property_filter]


def get_upcoming(days: int = 14, property_filter: str = "all") -> list[dict[str, Any]]:
    start, end = _window_dates(days)
    prop_sql, prop_args = _property_clause(property_filter)

    conn = get_connection()
    rows = conn.execute(
        f"""
        SELECT reservation_id, property_id, property_name, guest_name, arrival_date,
               departure_date, package_name, package_code, status, cancelled_at,
               source_updated_at, last_seen_at
        FROM reservations
        WHERE status != 'cancelled'
          AND arrival_date BETWEEN ? AND ?
          {prop_sql}
        ORDER BY arrival_date ASC, property_name ASC
        """,
        [start, end, *prop_args],
    ).fetchall()
    return [dict(r) for r in rows]


def get_cancelled(days: int = 14, property_filter: str = "all") -> list[dict[str, Any]]:
    start, end = _window_dates(days)
    prop_sql, prop_args = _property_clause(property_filter)

    conn = get_connection()
    rows = conn.execute(
        f"""
        SELECT reservation_id, property_id, property_name, guest_name, arrival_date,
               departure_date, package_name, package_code, status, cancelled_at,
               source_updated_at, last_seen_at
        FROM reservations
        WHERE status = 'cancelled'
          AND arrival_date BETWEEN ? AND ?
          {prop_sql}
        ORDER BY arrival_date ASC, cancelled_at DESC
        """,
        [start, end, *prop_args],
    ).fetchall()
    return [dict(r) for r in rows]
