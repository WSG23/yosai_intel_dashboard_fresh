from __future__ import annotations

from typing import Any, Dict, TYPE_CHECKING

from shared.events.names import EventName

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from yosai_intel_dashboard.src.services.analytics.protocols import PublishingProtocol


class EventPublisher:
    """Simple wrapper around a :class:`PublishingProtocol`."""

    def __init__(self, publisher: 'PublishingProtocol') -> None:
        self._publisher = publisher

    def publish(self, payload: Dict[str, Any], event: str = EventName.ANALYTICS_UPDATE) -> None:
        """Publish ``payload`` to the underlying publisher."""
        self._publisher.publish(payload, event)


__all__ = ["EventPublisher"]
