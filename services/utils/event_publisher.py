import logging
from typing import Any, Dict

from core.protocols import EventBusProtocol

logger = logging.getLogger(__name__)


def publish_event(
    event_bus: EventBusProtocol | None,
    payload: Dict[str, Any],
    event: str = "analytics_update",
) -> None:
    """Safely publish ``payload`` to ``event_bus`` if available."""
    if event_bus:
        try:
            event_bus.publish(event, payload)
        except Exception as exc:  # pragma: no cover - best effort
            logger.debug("Event bus publish failed: %s", exc)


__all__ = ["publish_event"]
