"""Convenience decorators for error handling."""

import asyncio
from functools import wraps
from typing import Any, Callable, TypeVar

from .core import ErrorHandler
from .exceptions import ErrorCategory

T = TypeVar("T")


def handle_errors(
    category: ErrorCategory = ErrorCategory.INTERNAL,
    reraise: bool = False,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Wrap *func* and convert exceptions into :class:`YosaiException`."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        handler = ErrorHandler()

        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001
                    err = handler.handle(exc, category)
                    if reraise:
                        raise err
                    return err  # type: ignore[return-value]

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001
                err = handler.handle(exc, category)
                if reraise:
                    raise err
                return err  # type: ignore[return-value]

        return sync_wrapper

    return decorator


__all__ = ["handle_errors"]
