import logging
from typing import Any, Dict

from shared.events.names import EventName

logger = logging.getLogger(__name__)


def publish_event(
    event_bus: Any | None,
    payload: Dict[str, Any],
    event: str = EventName.ANALYTICS_UPDATE,
) -> None:
    """Publish ``payload`` via the centralized :mod:`yosai_intel_dashboard.src.core.callbacks.event_bus`."""

    if event_bus:
        try:
            event_bus.emit(event, payload)
        except Exception as exc:  # pragma: no cover - best effort
            logger.debug("Event bus publish failed: %s", exc)

    try:
        from yosai_intel_dashboard.src.infrastructure.callbacks import (
            CallbackType,
            trigger_callback,
        )

        cb_event = CallbackType[event.upper()]
        trigger_callback(cb_event, payload)
    except KeyError:
        logger.debug("Unknown callback event: %s", event)
    except Exception as exc:  # pragma: no cover - best effort
        logger.debug("Callback dispatch failed: %s", exc)


__all__ = ["publish_event"]
