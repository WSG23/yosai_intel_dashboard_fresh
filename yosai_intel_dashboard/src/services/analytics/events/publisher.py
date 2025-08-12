from __future__ import annotations

from typing import Any, Dict

from shared.events.bus import EventBus
from shared.events.names import EventName
from yosai_intel_dashboard.src.services.event_publisher import publish_event


class Publisher:
    """Publish analytics updates to an event bus."""

    def __init__(self, event_bus: EventBus | None) -> None:
        self.event_bus = event_bus

    def publish(
        self, payload: Dict[str, Any], event: str = EventName.ANALYTICS_UPDATE
    ) -> None:
        publish_event(self.event_bus, payload, event)


__all__ = ["Publisher"]
