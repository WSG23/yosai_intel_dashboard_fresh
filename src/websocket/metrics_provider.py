"""Background publisher streaming metric updates over an event bus."""
from __future__ import annotations

import threading
from typing import Any, Dict, Protocol

from src.common.base import BaseComponent
from src.common.mixins import LoggingMixin, SerializationMixin


class EventBusProtocol(Protocol):
    def publish(self, event_type: str, data: Dict[str, Any]) -> None: ...


def generate_sample_metrics() -> Dict[str, Any]:
    """Return static metric payload for demonstration."""
    return {
        'performance': {'throughput': 100, 'latency_ms': 50},
        'drift': {'prediction_drift': 0.02},
        'feature_importance': {'age': 0.3}
    }


class MetricsProvider(LoggingMixin, SerializationMixin, BaseComponent):
    """Publish metrics updates to an event bus periodically."""

    def __init__(self, event_bus: EventBusProtocol, interval: float = 1.0) -> None:
        super().__init__(component_id="metrics_provider")
        self.event_bus = event_bus
        self.interval = interval
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self.log("MetricsProvider started")

    def _run(self) -> None:
        while not self._stop.is_set():
            payload = generate_sample_metrics()
            self.event_bus.publish('metrics_update', payload)
            self.log("Published metrics update")
            self._stop.wait(self.interval)

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=1)

    def to_dict(self) -> Dict[str, Any]:
        """Return serializable state for ``SerializationMixin``."""
        return {"interval": self.interval}


__all__ = ['MetricsProvider', 'generate_sample_metrics']
