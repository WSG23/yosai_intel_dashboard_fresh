from __future__ import annotations

"""Background publisher for demo analytics events.

This small utility periodically publishes sample analytics payloads on an event
bus.  It is intentionally lightweight and only implements the behaviour required
by the unit tests; the real project contains a far more feature rich version.
"""

import logging
import threading
from typing import Any, Dict

from src.common.base import BaseComponent
from src.common.config import ConfigProvider, ConfigService
from src.common.events import EventBus, EventPublisher
from yosai_intel_dashboard.src.services.analytics_summary import (
    generate_sample_analytics,
)


class WebSocketDataProvider(EventPublisher, BaseComponent):
    """Publish sample analytics updates to an event bus periodically."""

    def __init__(
        self,
        event_bus: EventBus,
        *,
        config: ConfigProvider | None = None,
        interval: float | None = None,
    ) -> None:
        BaseComponent.__init__(self, component_id="WebSocketDataProvider")
        EventPublisher.__init__(self, event_bus)
        self.config = config or ConfigService()
        self.interval = interval if interval is not None else self.config.metrics_interval


        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------
    def _run(self) -> None:
        while not self._stop.is_set():
            payload: Dict[str, Any] = generate_sample_analytics()
            self.publish_event("analytics_update", payload)

            logging.debug("analytics_update dispatched")
            self._stop.wait(self.interval)

    def stop(self) -> None:
        """Stop the provider thread."""
        self._stop.set()
        self._thread.join(timeout=1)


__all__ = ["WebSocketDataProvider"]
