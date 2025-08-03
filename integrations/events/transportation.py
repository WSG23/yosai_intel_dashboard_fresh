"""Connector for transportation schedule events."""

from __future__ import annotations

from datetime import datetime

from database.events import EventRecord


def fetch_events() -> list[EventRecord]:
    """Return transportation-related events."""
    return [
        EventRecord(
            name="VIP Arrival",
            start=datetime(2024, 1, 15, 7, 30),
            category="VIP",
        )
    ]
