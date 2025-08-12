from __future__ import annotations

from typing import Any, Dict

from src.common import BaseComponent, EventDispatchMixin, handle_deprecated
from yosai_intel_dashboard.src.core.interfaces.protocols import EventBusProtocol
from yosai_intel_dashboard.src.services.analytics.protocols import PublishingProtocol
from shared.events import publish_event


class PublishingService(EventDispatchMixin, BaseComponent, PublishingProtocol):
    """Service wrapping :class:`Publisher` for event dispatch."""

    @handle_deprecated("event_bus")
    def __init__(self, *, event_bus: EventBusProtocol | None = None) -> None:
        super().__init__(event_bus=event_bus)

    def publish(self, payload: Dict[str, Any], event: str = "analytics_update") -> None:
        publish_event(self.event_bus, payload, event)


__all__ = ["PublishingService"]
