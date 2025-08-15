"""ISP status page client."""

from __future__ import annotations

from typing import List

from yosai_intel_dashboard.src.database.infrastructure_events import (
    InfrastructureEvent,
    record_event,
)


class ISPStatusClient:
    """Fetch ISP service degradation reports."""

    def fetch_events(self) -> List[InfrastructureEvent]:  # pragma: no cover - network
        """Retrieve ISP status page events."""
        return []

    def ingest(self) -> None:
        """Fetch events and store them in the infrastructure event store."""
        for event in self.fetch_events():
            record_event(event)
