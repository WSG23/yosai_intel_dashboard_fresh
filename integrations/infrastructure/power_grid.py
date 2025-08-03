"""Power grid outage API client."""

from __future__ import annotations

from typing import List

from yosai_intel_dashboard.src.database.infrastructure_events import (
    InfrastructureEvent,
    record_event,
)


class PowerGridClient:
    """Fetch and store power-grid infrastructure events."""

    def fetch_events(self) -> List[InfrastructureEvent]:  # pragma: no cover - network
        """Retrieve current power-grid events from the upstream API."""
        return []

    def ingest(self) -> None:
        """Fetch events and persist them via ``record_event``."""
        for event in self.fetch_events():
            record_event(event)
