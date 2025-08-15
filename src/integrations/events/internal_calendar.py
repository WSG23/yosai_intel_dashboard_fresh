"""Connector for internal calendar events."""

from __future__ import annotations

from datetime import datetime

from yosai_intel_dashboard.src.database.events import EventRecord


def fetch_events() -> list[EventRecord]:
    """Return upcoming internal calendar events."""
    return [
        EventRecord(
            name="Board Meeting",
            start=datetime(2024, 1, 15, 9, 0),
            category="meetings",
        )
    ]
