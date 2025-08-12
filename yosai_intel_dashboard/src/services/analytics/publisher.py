from __future__ import annotations

from typing import Any, Dict

from yosai_intel_dashboard.src.services.event_publisher import publish_event
from yosai_intel_dashboard.src.services.analytics.core.interfaces import EventBusProtocol
from shared.events.names import EventName


class Publisher:
    """Publish analytics updates to an event bus."""

    def __init__(self, event_bus: Any | None = None) -> None:
        self.event_bus = event_bus

    def publish(
        self, payload: Dict[str, Any], event: str = EventName.ANALYTICS_UPDATE
    ) -> None:
        publish_event(self.event_bus, payload, event)


def create_publisher(event_bus: EventBusProtocol | None = None) -> "Publisher":
    """Create a :class:`Publisher` with default dependencies."""
    return Publisher(event_bus)


__all__ = ["Publisher", "create_publisher"]
