from __future__ import annotations

import asyncio
import inspect
import time
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict, List, Tuple


Callback = Callable[..., Any]


class EventBus:
    """Simple publish/subscribe event bus."""

    def __init__(self) -> None:
        self._subscribers: Dict[Any, List[Tuple[int, Callback]]] = defaultdict(list)
        self._metrics: Dict[Any, Dict[str, float]] = defaultdict(
            lambda: {"calls": 0, "exceptions": 0, "total_time": 0.0}
        )

    # ------------------------------------------------------------------
    def subscribe(self, event: Any, func: Callback, *, priority: int = 50) -> None:
        """Subscribe *func* to *event* with optional *priority*."""

        subs = self._subscribers[event]
        subs.append((priority, func))
        subs.sort(key=lambda x: x[0])

    def unsubscribe(self, event: Any, func: Callback) -> None:
        """Unsubscribe *func* from *event*."""

        self._subscribers[event] = [
            (p, f) for p, f in self._subscribers.get(event, []) if f != func
        ]

    # ------------------------------------------------------------------
    def emit(self, event: Any, *args: Any, **kwargs: Any) -> List[Any]:
        """Synchronously emit *event* to all subscribers."""

        results: List[Any] = []
        callbacks = list(self._subscribers.get(event, []))
        for _, cb in callbacks:
            start = time.perf_counter()
            try:
                if inspect.iscoroutinefunction(cb):
                    result = asyncio.run(cb(*args, **kwargs))
                else:
                    result = cb(*args, **kwargs)
                duration = time.perf_counter() - start
                metric = self._metrics[event]
                metric["calls"] += 1
                metric["total_time"] += duration
                results.append(result)
            except Exception:
                metric = self._metrics[event]
                metric["calls"] += 1
                metric["exceptions"] += 1
                results.append(None)
        return results

    async def emit_async(self, event: Any, *args: Any, **kwargs: Any) -> List[Any]:
        """Asynchronously emit *event* to all subscribers."""

        results: List[Any] = []
        for _, cb in self._subscribers.get(event, []):
            start = time.perf_counter()
            try:
                if inspect.iscoroutinefunction(cb):
                    result = await cb(*args, **kwargs)
                else:
                    result = cb(*args, **kwargs)
                duration = time.perf_counter() - start
                metric = self._metrics[event]
                metric["calls"] += 1
                metric["total_time"] += duration
                results.append(result)
            except Exception:
                metric = self._metrics[event]
                metric["calls"] += 1
                metric["exceptions"] += 1
                results.append(None)
        return results

    def get_callbacks(self, event: Any) -> List[Callback]:
        """Return callbacks subscribed to *event*."""

        return [cb for _, cb in self._subscribers.get(event, [])]

    def get_metrics(self, event: Any) -> Dict[str, float]:
        """Return metrics for *event*."""

        return self._metrics[event]

    def clear(self) -> None:
        """Remove all subscriptions and metrics."""

        self._subscribers.clear()
        self._metrics.clear()


class EventPublisher:
    """Mixin providing convenient access to an :class:`EventBus`."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self.event_bus = event_bus or EventBus()

    def emit_event(self, event: Any, *args: Any, **kwargs: Any) -> List[Any]:
        """Emit *event* on the configured :class:`EventBus`."""

        return self.event_bus.emit(event, *args, **kwargs)
