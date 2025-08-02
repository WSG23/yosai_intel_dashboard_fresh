from __future__ import annotations

from typing import Any, Awaitable, Callable, TypeVar

from monitoring.performance_profiler import PerformanceProfiler

T = TypeVar("T")

_profiler = PerformanceProfiler()


class AsyncContextManager:
    """Generic asynchronous context manager wrapper."""

    def __init__(
        self,
        enter: Callable[[], Awaitable[T]],
        exit: Callable[[Any, Any, Any], Awaitable[None]],
    ) -> None:
        self._enter = enter
        self._exit = exit

    async def __aenter__(self) -> T:
        async with _profiler.track_task("async_context_enter"):
            return await self._enter()

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        async with _profiler.track_task("async_context_exit"):
            await self._exit(exc_type, exc, tb)
