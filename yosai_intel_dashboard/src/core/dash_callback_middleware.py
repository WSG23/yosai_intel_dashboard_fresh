from __future__ import annotations

"""Utilities to wrap Dash callbacks with validation and error handling."""

import asyncio
from typing import Any, Callable, Iterable, Tuple

from dash import Output, no_update

from validation.security_validator import SecurityValidator

from .error_handling import ErrorSeverity, error_handler

SafeReturn = Any


def _sanitize_value(value: Any, name: str, validator: SecurityValidator) -> Any:
    if isinstance(value, str):
        result = validator.validate_input(value, name)
        return result.get("sanitized", value)
    return value


def _sanitize_args(
    args: Iterable[Any], validator: SecurityValidator
) -> tuple[Any, ...]:
    sanitized = []
    for i, val in enumerate(args):
        sanitized.append(_sanitize_value(val, f"arg{i}", validator))
    return tuple(sanitized)


def _sanitize_kwargs(
    kwargs: dict[str, Any], validator: SecurityValidator
) -> dict[str, Any]:
    return {k: _sanitize_value(v, k, validator) for k, v in kwargs.items()}


def wrap_callback(
    func: Callable[..., Any],
    outputs: Tuple[Output, ...],
    validator: SecurityValidator,
) -> Callable[..., SafeReturn]:
    """Wrap a Dash callback with validation and error logging."""

    safe_default: SafeReturn
    default_tuple = tuple(no_update for _ in outputs)
    safe_default = default_tuple[0] if len(default_tuple) == 1 else default_tuple

    async def _async_wrapper(*args: Any, **kwargs: Any) -> SafeReturn:
        try:
            s_args = _sanitize_args(args, validator)
            s_kwargs = _sanitize_kwargs(kwargs, validator)
            return await func(*s_args, **s_kwargs)
        except Exception as exc:  # noqa: BLE001
            error_handler.handle_error(
                exc,
                severity=ErrorSeverity.HIGH,
                context={"callback": getattr(func, "__name__", "<anonymous>")},
            )
            return safe_default

    def _sync_wrapper(*args: Any, **kwargs: Any) -> SafeReturn:
        try:
            s_args = _sanitize_args(args, validator)
            s_kwargs = _sanitize_kwargs(kwargs, validator)
            return func(*s_args, **s_kwargs)
        except Exception as exc:  # noqa: BLE001
            error_handler.handle_error(
                exc,
                severity=ErrorSeverity.HIGH,
                context={"callback": getattr(func, "__name__", "<anonymous>")},
            )
            return safe_default

    return _async_wrapper if asyncio.iscoroutinefunction(func) else _sync_wrapper


__all__ = ["wrap_callback"]
