"""Background publisher streaming metric updates over an event bus."""

from __future__ import annotations

import threading
import warnings
from typing import Any, Dict, Protocol

from src.common.base import BaseComponent
from src.common.mixins import LoggingMixin, SerializationMixin
from src.repository import InMemoryMetricsRepository, MetricsRepository


class EventBusProtocol(Protocol):
    def publish(self, event_type: str, data: Dict[str, Any]) -> None: ...


class MetricsProvider(LoggingMixin, SerializationMixin, BaseComponent):
    """Publish metrics updates to an event bus periodically."""

    def __init__(
        self,
        event_bus: EventBusProtocol,
        repo: MetricsRepository | None = None,
        *,
        interval: float = 1.0,
    ) -> None:
        if repo is None:
            warnings.warn(
                "MetricsProvider now requires a repository; default will be removed",
                DeprecationWarning,
                stacklevel=2,
            )
            repo = InMemoryMetricsRepository()
        super().__init__(
            component_id="metrics_provider",
            event_bus=event_bus,
            repo=repo,
            interval=interval,
        )

        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self.log("MetricsProvider started")

    def _run(self) -> None:
        while not self._stop.is_set():
            payload = self.repo.snapshot()
            self.event_bus.publish("metrics_update", payload)
            self.log("Published metrics update")

            self._stop.wait(self.interval)

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=1)

    def to_dict(self) -> Dict[str, Any]:
        """Return serializable state for ``SerializationMixin``."""
        return {"interval": self.interval}


__all__ = ["MetricsProvider"]
