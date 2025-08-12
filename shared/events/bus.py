"""Event bus utilities.

Provides :class:`EventBus` and :class:`EventPublisher` for simple
publish/subscribe communication with optional async support. Callbacks can be
throttled and per-event metrics are collected. See
``docs/callback_architecture.md`` for an architectural overview.
"""

from __future__ import annotations

import asyncio
import inspect
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

Callback = Callable[..., Any]


@dataclass
class _Subscriber:
    priority: int
    callback: Callback
    throttle: float | None = None
    last_call: float = 0.0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class EventBus:
    """Simple publish/subscribe event bus with async support and throttling."""

    def __init__(self, *, max_concurrency: Optional[int] = None) -> None:
        self._subscribers: Dict[Any, List[_Subscriber]] = defaultdict(list)
        self._metrics: Dict[Any, Dict[str, float]] = defaultdict(
            lambda: {"calls": 0, "exceptions": 0, "total_time": 0.0, "throttled": 0}
        )
        self._semaphore: Optional[asyncio.Semaphore] = (
            asyncio.Semaphore(max_concurrency) if max_concurrency else None
        )

    # ------------------------------------------------------------------
    def subscribe(
        self,
        event: Any,
        func: Callback,
        *,
        priority: int = 50,
        throttle: float | None = None,
    ) -> None:
        """Subscribe *func* to *event* with optional *priority* and *throttle* interval."""

        subs = self._subscribers[event]
        subs.append(_Subscriber(priority, func, throttle))
        subs.sort(key=lambda s: s.priority)

    async def subscribe_async(
        self,
        event: Any,
        func: Callback,
        *,
        priority: int = 50,
        throttle: float | None = None,
    ) -> None:
        """Asynchronously subscribe *func* to *event*.

        Provided for API symmetry; simply delegates to :meth:`subscribe`.
        """

        self.subscribe(event, func, priority=priority, throttle=throttle)

    def unsubscribe(self, event: Any, func: Callback) -> None:
        """Unsubscribe *func* from *event*."""

        self._subscribers[event] = [
            s for s in self._subscribers.get(event, []) if s.callback != func
        ]

    # ------------------------------------------------------------------
    def publish(self, event: Any, *args: Any, **kwargs: Any) -> List[Any]:
        """Synchronously publish *event* to all subscribers."""

        results: List[Any] = []
        for sub in list(self._subscribers.get(event, [])):
            if not self._should_invoke(event, sub):
                continue
            results.append(self._invoke(event, sub.callback, *args, **kwargs))
        return results

    async def publish_async(self, event: Any, *args: Any, **kwargs: Any) -> List[Any]:
        """Asynchronously publish *event* to all subscribers."""

        tasks = []
        for sub in self._subscribers.get(event, []):
            if not self._should_invoke(event, sub):
                continue

            async def invoke(sub=sub):
                if self._semaphore:
                    async with self._semaphore:
                        async with sub.lock:
                            return await self._invoke_async(
                                event, sub.callback, *args, **kwargs
                            )
                async with sub.lock:
                    return await self._invoke_async(event, sub.callback, *args, **kwargs)

            tasks.append(asyncio.create_task(invoke()))

        if tasks:
            return await asyncio.gather(*tasks)
        return []

    # ------------------------------------------------------------------
    def _should_invoke(self, event: Any, sub: _Subscriber) -> bool:
        if sub.throttle is not None:
            now = time.perf_counter()
            if now - sub.last_call < sub.throttle:
                metric = self._metrics[event]
                metric["throttled"] += 1
                return False
            sub.last_call = now
        return True

    def _update_metrics(
        self,
        event: Any,
        *,
        duration: float | None = None,
        error: bool = False,
    ) -> None:
        """Update metrics for a callback invocation."""

        metric = self._metrics[event]
        metric["calls"] += 1
        if error:
            metric["exceptions"] += 1
        if duration is not None:
            metric["total_time"] += duration

    def _invoke(self, event: Any, callback: Callback, *args: Any, **kwargs: Any) -> Any:
        """Invoke *callback* synchronously and record metrics."""

        start = time.perf_counter()
        try:
            if inspect.iscoroutinefunction(callback):
                result = asyncio.run(callback(*args, **kwargs))
            else:
                result = callback(*args, **kwargs)
            self._update_metrics(event, duration=time.perf_counter() - start)
            return result
        except Exception:
            self._update_metrics(event, error=True)
            return None

    async def _invoke_async(
        self, event: Any, callback: Callback, *args: Any, **kwargs: Any
    ) -> Any:
        """Invoke *callback* asynchronously and record metrics."""

        start = time.perf_counter()
        try:
            if inspect.iscoroutinefunction(callback):
                result = await callback(*args, **kwargs)
            else:
                result = callback(*args, **kwargs)
            self._update_metrics(event, duration=time.perf_counter() - start)
            return result
        except Exception:
            self._update_metrics(event, error=True)
            return None

    # ------------------------------------------------------------------
    def get_callbacks(self, event: Any) -> List[Callback]:
        """Return callbacks subscribed to *event*."""

        return [s.callback for s in self._subscribers.get(event, [])]

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

    def publish_event(self, event: Any, *args: Any, **kwargs: Any) -> List[Any]:
        """Publish *event* on the configured :class:`EventBus`."""

        return self.event_bus.publish(event, *args, **kwargs)

    async def publish_event_async(self, event: Any, *args: Any, **kwargs: Any) -> List[Any]:
        """Asynchronously publish *event* on the configured :class:`EventBus`."""

        return await self.event_bus.publish_async(event, *args, **kwargs)


__all__ = ["EventBus", "EventPublisher"]
