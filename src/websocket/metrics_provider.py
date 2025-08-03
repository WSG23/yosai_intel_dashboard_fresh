"""Background publisher streaming metric updates over an event bus."""
from __future__ import annotations

import logging
import threading
from typing import Any, Dict

from src.repository import MetricsRepository


class EventBusProtocol(Protocol):
    def publish(self, event_type: str, data: Dict[str, Any]) -> None: ...


class MetricsProvider:
    """Publish metrics updates to an event bus periodically."""

    def __init__(self, event_bus: EventBusProtocol, repo: MetricsRepository, interval: float = 1.0) -> None:
        self.event_bus = event_bus
        self.repo = repo

        self.interval = interval

        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            payload = self.repo.snapshot()
            self.event_bus.publish("metrics_update", payload)

            self._stop.wait(self.interval)

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=1)


__all__ = ["MetricsProvider"]
