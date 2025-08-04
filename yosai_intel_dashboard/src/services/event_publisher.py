import logging
from typing import Dict

logger = logging.getLogger(__name__)


def publish_event(
    event_bus: Any | None,
    payload: Dict[str, Any],
    event: str = "analytics_update",
) -> None:
    """Trigger a callback for ``event`` if registered."""
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
