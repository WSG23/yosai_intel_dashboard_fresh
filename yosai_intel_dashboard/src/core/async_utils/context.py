from __future__ import annotations

"""Helpers for building asynchronous context managers."""

from typing import Awaitable, Callable, Generic, TypeVar

T = TypeVar("T")


class AsyncContextManager(Generic[T]):
    """Create an async context manager from enter and exit callables."""

    def __init__(
        self,
        enter: Callable[[], Awaitable[T]] | None = None,
        exit: Callable[[BaseException | None], Awaitable[None]] | None = None,
    ) -> None:
        self._enter = enter
        self._exit = exit

    async def __aenter__(self) -> T | None:
        if self._enter:
            return await self._enter()
        return None

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object | None,
    ) -> None:
        if self._exit:
            await self._exit(exc)


__all__ = ["AsyncContextManager"]
