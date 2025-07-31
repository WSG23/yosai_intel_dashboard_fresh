from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Tuple

from .base_model import BaseModel
from .callback_events import CallbackEvent

logger = logging.getLogger(__name__)


class CallbackManager(BaseModel):
    """Thread-safe event callback manager."""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self._callbacks: Dict[CallbackEvent, List[Tuple[int, Callable[..., Any]]]] = (
            defaultdict(list)
        )
        self._metrics: Dict[CallbackEvent, Dict[str, float | int]] = defaultdict(
            lambda: {"calls": 0, "exceptions": 0, "total_time": 0.0}
        )
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    def handle_register(
        self, event: CallbackEvent, func: Callable[..., Any], *, priority: int = 50
    ) -> None:
        """Register a callback for an event with optional priority."""
        with self._lock:
            self._callbacks[event].append((priority, func))
            self._callbacks[event].sort(key=lambda x: x[0])

    # ------------------------------------------------------------------
    def handle_unregister(self, event: CallbackEvent, func: Callable[..., Any]) -> None:
        """Unregister a previously registered callback."""
        with self._lock:
            self._callbacks[event] = [
                (p, f) for p, f in self._callbacks.get(event, []) if f != func
            ]

    # ------------------------------------------------------------------
    def _record_metric(
        self, event: CallbackEvent, start: float, error: bool = False
    ) -> None:
        metric = self._metrics[event]
        metric["calls"] += 1
        if error:
            metric["exceptions"] += 1
        metric["total_time"] += time.perf_counter() - start

    # ------------------------------------------------------------------
    def trigger(self, event: CallbackEvent, *args: Any, **kwargs: Any) -> List[Any]:
        """Synchronously trigger callbacks for an event."""
        results = []
        callbacks = self.get_callbacks(event)
        for _, func in callbacks:
            start = time.perf_counter()
            try:
                if asyncio.iscoroutinefunction(func):
                    result = asyncio.run(func(*args, **kwargs))
                else:
                    result = func(*args, **kwargs)
                results.append(result)
                self._record_metric(event, start)
            except Exception as exc:  # pragma: no cover - log and continue
                logger.exception(f"Callback error on {event.name}: {exc}")
                self._record_metric(event, start, error=True)
                results.append(None)
        return results

    # ------------------------------------------------------------------
    async def trigger_async(
        self, event: CallbackEvent, *args: Any, **kwargs: Any
    ) -> List[Any]:
        """Asynchronously trigger callbacks for an event."""
        results = []
        callbacks = self.get_callbacks(event)
        for _, func in callbacks:
            start = time.perf_counter()
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                results.append(result)
                self._record_metric(event, start)
            except Exception as exc:  # pragma: no cover - log and continue
                logger.exception(f"Callback error on {event.name}: {exc}")
                self._record_metric(event, start, error=True)
                results.append(None)
        return results

    # ------------------------------------------------------------------
    def get_callbacks(
        self, event: CallbackEvent
    ) -> List[Tuple[int, Callable[..., Any]]]:
        with self._lock:
            return list(self._callbacks.get(event, []))

    # ------------------------------------------------------------------
    def get_metrics(self, event: CallbackEvent) -> Dict[str, float | int]:
        with self._lock:
            return dict(self._metrics.get(event, {}))
