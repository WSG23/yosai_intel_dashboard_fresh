from __future__ import annotations

from typing import Any, Dict

from yosai_intel_dashboard.src.core.interfaces.protocols import EventBusProtocol
from yosai_intel_dashboard.src.services.event_publisher import publish_event


class Publisher:
    """Publish analytics updates to an event bus."""

    def __init__(self, event_bus: EventBusProtocol | None) -> None:
        self.event_bus = event_bus

    def publish(self, payload: Dict[str, Any], event: str = "analytics_update") -> None:
        publish_event(self.event_bus, payload, event)


__all__ = ["Publisher"]
