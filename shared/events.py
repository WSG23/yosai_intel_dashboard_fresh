"""Shared event publishing utilities."""

from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any, Mapping

logger = logging.getLogger(__name__)


def _maybe_async(result: Any) -> None:
    if inspect.isawaitable(result):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(result)
        except RuntimeError:  # no running event loop
            asyncio.run(result)


def publish_event(
    event_bus: Any | None,
    payload: Mapping[str, Any],
    event: str = "analytics_update",
) -> None:
    """Safely publish ``payload`` via ``event_bus`` and callbacks.

    Any coroutine returned by the event bus or callback dispatcher is scheduled
    on the running loop or executed synchronously if no loop is present.
    """
    if event_bus:
        try:
            publish = getattr(event_bus, "emit", None) or getattr(event_bus, "publish", None)
            if publish:
                _maybe_async(publish(event, payload))
        except Exception as exc:  # pragma: no cover - best effort
            logger.debug("Event bus publish failed: %s", exc)
    try:
        from yosai_intel_dashboard.src.infrastructure.callbacks import (
            CallbackType,
            trigger_callback,
        )

        cb_event = CallbackType[event.upper()]
        _maybe_async(trigger_callback(cb_event, payload))
    except KeyError:
        logger.debug("Unknown callback event: %s", event)
    except Exception as exc:  # pragma: no cover - best effort
        logger.debug("Callback dispatch failed: %s", exc)


__all__ = ["publish_event"]
