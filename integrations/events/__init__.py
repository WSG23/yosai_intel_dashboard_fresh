"""Event integration connectors and ingestion utilities."""

from __future__ import annotations

from database.events import add_events

from .internal_calendar import fetch_events as fetch_internal_calendar
from .public_api import fetch_events as fetch_public_api
from .transportation import fetch_events as fetch_transportation_schedule


def ingest_all() -> None:
    """Fetch events from all connectors and store them."""
    events = []
    events.extend(fetch_internal_calendar())
    events.extend(fetch_public_api())
    events.extend(fetch_transportation_schedule())
    add_events(events)
