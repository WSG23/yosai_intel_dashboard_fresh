"""Background publisher streaming metric updates over an event bus."""
from __future__ import annotations

import logging
import threading
from typing import Any, Dict

from src.common.events import EventBus, EventPublisher


def generate_sample_metrics() -> Dict[str, Any]:
    """Return static metric payload for demonstration."""
    return {
        'performance': {'throughput': 100, 'latency_ms': 50},
        'drift': {'prediction_drift': 0.02},
        'feature_importance': {'age': 0.3}
    }


class MetricsProvider(EventPublisher):
    """Publish metrics updates to an event bus periodically."""

    def __init__(self, event_bus: EventBus, interval: float = 1.0) -> None:
        super().__init__(event_bus)
        self.interval = interval

        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            payload = generate_sample_metrics()
            self.publish_event('metrics_update', payload)

            self._stop.wait(self.interval)

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=1)


__all__ = ['MetricsProvider', 'generate_sample_metrics']
