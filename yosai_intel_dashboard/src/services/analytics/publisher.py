from __future__ import annotations

from typing import Any, Dict

from shared.events.bus import EventPublisher
from shared.events.names import EventName


class Publisher(EventPublisher):
    """Publish analytics updates to an event bus."""

    def __init__(self, event_bus: Any | None = None) -> None:
        super().__init__(event_bus)

    def publish(
        self, payload: Dict[str, Any], event: str = EventName.ANALYTICS_UPDATE
    ) -> None:
        self.publish_event(event, payload)


def create_publisher(event_bus: Any | None = None) -> "Publisher":
    """Create a :class:`Publisher` with default dependencies."""
    return Publisher(event_bus)


__all__ = ["Publisher", "create_publisher"]
