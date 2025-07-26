from __future__ import annotations

"""Utilities for running asynchronous operations in bulk."""

import asyncio
from typing import Awaitable, Callable, Iterable, List, Any


class AsyncBatch:
    """Collect coroutines and execute them concurrently."""

    def __init__(self, limit: int | None = None) -> None:
        self._limit = limit
        self._sem = asyncio.Semaphore(limit) if limit else None
        self._tasks: List[Awaitable[Any]] = []

    async def _wrap(self, coro: Awaitable[Any]) -> Any:
        if self._sem:
            async with self._sem:
                return await coro
        return await coro

    def add(self, coro: Awaitable[Any]) -> None:
        self._tasks.append(self._wrap(coro))

    async def run(self) -> List[Any]:
        results = await asyncio.gather(*self._tasks)
        self._tasks.clear()
        return results

    async def map(self, funcs: Iterable[Callable[[], Awaitable[Any]]]) -> List[Any]:
        for func in funcs:
            self.add(func())
        return await self.run()


__all__ = ["AsyncBatch"]
