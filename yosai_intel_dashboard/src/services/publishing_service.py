from __future__ import annotations

from typing import Any, Dict

from src.common.base import BaseComponent
from shared.events.bus import EventPublisher
from shared.events.names import EventName
from yosai_intel_dashboard.src.core.interfaces.protocols import EventBusProtocol
from yosai_intel_dashboard.src.services.analytics.protocols import PublishingProtocol


class PublishingService(EventPublisher, BaseComponent, PublishingProtocol):
    """Publish analytics events via the shared :class:`EventBus`."""

    def __init__(self, event_bus: EventBusProtocol | None = None) -> None:
        EventPublisher.__init__(self, event_bus)
        BaseComponent.__init__(self, event_bus=event_bus)

    def publish(self, payload: Dict[str, Any], event: str = EventName.ANALYTICS_UPDATE) -> None:
        self.publish_event(event, payload)


__all__ = ["PublishingService"]
