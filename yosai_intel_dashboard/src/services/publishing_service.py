from __future__ import annotations

from typing import Any, Dict

from yosai_intel_dashboard.src.core.interfaces.protocols import EventBusProtocol
from yosai_intel_dashboard.src.services.analytics.protocols import PublishingProtocol
from yosai_intel_dashboard.src.services.analytics.publisher import Publisher


class PublishingService(PublishingProtocol):
    """Service wrapping :class:`Publisher` for event dispatch."""

    def __init__(self, event_bus: EventBusProtocol | None = None) -> None:
        self._publisher = Publisher(event_bus)

    def publish(self, payload: Dict[str, Any], event: str = "analytics_update") -> None:
        self._publisher.publish(payload, event)


__all__ = ["PublishingService"]
