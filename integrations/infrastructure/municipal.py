"""Municipal alert feed client."""

from __future__ import annotations

from typing import List

from yosai_intel_dashboard.src.database.infrastructure_events import (
    InfrastructureEvent,
    record_event,
)


class MunicipalAlertClient:
    """Consume municipal alert feeds for outages or emergencies."""

    def fetch_events(self) -> List[InfrastructureEvent]:  # pragma: no cover - network
        """Fetch municipal infrastructure alerts."""
        return []

    def ingest(self) -> None:
        """Fetch events and record them via ``record_event``."""
        for event in self.fetch_events():
            record_event(event)
