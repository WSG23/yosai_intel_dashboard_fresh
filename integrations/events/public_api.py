"""Connector for public event APIs."""

from __future__ import annotations

from datetime import datetime

from database.events import EventRecord


def fetch_events() -> list[EventRecord]:
    """Return events from public APIs."""
    return [
        EventRecord(
            name="City Marathon",
            start=datetime(2024, 1, 15, 8, 0),
            category="sports",
        ),
        EventRecord(
            name="Independence Day",
            start=datetime(2024, 7, 4, 0, 0),
            category="holidays",
        ),
    ]
