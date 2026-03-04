from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path("dashboard.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reservation_id TEXT NOT NULL,
                property_id TEXT NOT NULL,
                property_name TEXT NOT NULL,
                guest_name TEXT,
                arrival_date TEXT NOT NULL,
                departure_date TEXT,
                package_name TEXT,
                package_code TEXT,
                status TEXT NOT NULL,
                cancelled_at TEXT,
                source_updated_at TEXT,
                last_seen_at TEXT NOT NULL,
                raw_payload TEXT
            )
            """
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_reservation_property ON reservations (reservation_id, property_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_arrival_property_status ON reservations (arrival_date, property_id, status)"
        )
