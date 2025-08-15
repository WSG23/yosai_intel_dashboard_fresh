"""Helper utilities for callback execution."""

from __future__ import annotations

import asyncio
from typing import Any, Callable, TypeVar

from ...core.error_handling import ErrorSeverity, error_handler

T = TypeVar("T")


def safe_execute(
    func: Callable[..., T],
    *args: Any,
    context: dict[str, Any] | None = None,
    default: T | None = None,
    **kwargs: Any,
) -> tuple[T | None, bool]:
    """Execute ``func`` and route exceptions to the global error handler.

    Parameters
    ----------
    func:
        Callable to execute.
    context:
        Optional context dictionary passed to the error handler.
    default:
        Value returned when ``func`` raises an exception.

    Returns
    -------
    tuple[T | None, bool]
        A tuple of the function result (or ``default``) and a success flag.
    """

    try:
        return func(*args, **kwargs), True
    except Exception as exc:  # noqa: BLE001
        error_handler.handle_error(
            exc,
            severity=ErrorSeverity.HIGH,
            context=context or {},
        )
        return default, False


async def safe_execute_async(
    func: Callable[..., T],
    *args: Any,
    context: dict[str, Any] | None = None,
    default: T | None = None,
    **kwargs: Any,
) -> tuple[T | None, bool]:
    """Asynchronous variant of :func:`safe_execute`."""

    try:
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs), True
        return func(*args, **kwargs), True
    except Exception as exc:  # noqa: BLE001
        error_handler.handle_error(
            exc,
            severity=ErrorSeverity.HIGH,
            context=context or {},
        )
        return default, False


__all__ = ["safe_execute", "safe_execute_async"]

