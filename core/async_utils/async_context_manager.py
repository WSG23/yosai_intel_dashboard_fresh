from __future__ import annotations

from typing import Any, Awaitable, Callable, TypeVar

T = TypeVar("T")


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
        return await self._enter()

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self._exit(exc_type, exc, tb)
