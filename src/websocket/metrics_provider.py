"""Background publisher streaming metric updates over an event bus."""

from __future__ import annotations

import threading
from typing import Any, Dict


from src.common.base import BaseComponent
from shared.events.bus import EventBus, EventPublisher
from src.common.mixins import LoggingMixin, SerializationMixin
from src.repository import InMemoryMetricsRepository


def generate_sample_metrics() -> Dict[str, Any]:
    """Return static metric payload for demonstration."""
    return InMemoryMetricsRepository().snapshot()


class MetricsProvider(EventPublisher, LoggingMixin, SerializationMixin, BaseComponent):

    """Publish metrics updates to an event bus periodically."""

    def __init__(
        self,
        event_bus: EventBus,
        repo: Any | None = None,
        interval: float = 1.0,
    ) -> None:
        BaseComponent.__init__(
            self,
            component_id="metrics_provider",
            event_bus=event_bus,
            repo=repo or InMemoryMetricsRepository(),
            interval=interval,
        )


        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self.log("MetricsProvider started")

    def _run(self) -> None:
        while not self._stop.is_set():
            payload = self.repo.snapshot()
            self.publish_event("metrics_update", payload)

            self.log("Published metrics update")

            self._stop.wait(self.interval)

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=1)

    def to_dict(self) -> Dict[str, Any]:
        """Return serializable state for ``SerializationMixin``."""
        return {"interval": self.interval}


__all__ = ["MetricsProvider"]
