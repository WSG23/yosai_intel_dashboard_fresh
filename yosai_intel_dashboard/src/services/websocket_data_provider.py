from __future__ import annotations

"""Simple background publisher for analytics WebSocket demos."""

import threading
import time
from typing import Any, Dict

from yosai_intel_dashboard.src.core.interfaces.protocols import EventBusProtocol
from yosai_intel_dashboard.src.services.analytics_summary import generate_sample_analytics
from src.common.base import BaseComponent
from src.common.config import ConfigProvider


class WebSocketDataProvider(BaseComponent):
    """Publish sample analytics updates to an event bus periodically."""

    def __init__(
        self,
        event_bus: EventBusProtocol,
        *,
        config: ConfigProvider | None = None,
        interval: float | None = None,
    ) -> None:
        super().__init__(config)
        self.event_bus = event_bus
        self.interval = interval if interval is not None else self.config.metrics_interval
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            payload: Dict[str, Any] = generate_sample_analytics()
            self.event_bus.publish("analytics_update", payload)
            self._stop.wait(self.interval)

    def stop(self) -> None:
        """Stop the provider thread."""
        self._stop.set()
        self._thread.join(timeout=1)


__all__ = ["WebSocketDataProvider"]
