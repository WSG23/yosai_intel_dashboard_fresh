import logging
from typing import Dict

from src.common.events import EventBus

logger = logging.getLogger(__name__)


def publish_event(
    event_bus: EventBus | None,
    payload: Dict[str, Any],
    event: str = "analytics_update",
) -> None:
    """Safely publish ``payload`` to ``event_bus`` if available."""
    if event_bus:
        try:
            event_bus.emit(event, payload)
        except Exception as exc:  # pragma: no cover - best effort
            logger.debug("Event bus publish failed: %s", exc)


__all__ = ["publish_event"]
