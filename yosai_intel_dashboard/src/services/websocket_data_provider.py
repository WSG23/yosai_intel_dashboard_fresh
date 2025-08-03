from __future__ import annotations

"""Simple background publisher for analytics WebSocket demos."""

import logging
import threading
from typing import Any, Dict

from src.common import (
    BaseComponent,
    EventDispatchMixin,
    LoggingMixin,
    handle_deprecated,
)
from yosai_intel_dashboard.src.core.interfaces.protocols import EventBusProtocol
from yosai_intel_dashboard.src.services.analytics_summary import generate_sample_analytics


class WebSocketDataProvider(EventDispatchMixin, LoggingMixin, BaseComponent):
    """Publish sample analytics updates to an event bus periodically."""

    @handle_deprecated("event_bus", "interval")
    def __init__(self, *, event_bus: EventBusProtocol, interval: float = 1.0) -> None:
        super().__init__(event_bus=event_bus, interval=interval)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            payload: Dict[str, Any] = generate_sample_analytics()
            self.dispatch_event("analytics_update", payload)
            self.log(logging.DEBUG, "analytics_update dispatched")
            self._stop.wait(self.interval)

    def stop(self) -> None:
        """Stop the provider thread."""
        self._stop.set()
        self._thread.join(timeout=1)


__all__ = ["WebSocketDataProvider"]
