from __future__ import annotations

"""Lightweight public interface for the callback system.

This module exposes convenience functions that wrap a module level instance of
:class:`TrulyUnifiedCallbacks`.  It allows legacy code to register and trigger
callbacks without needing to manage a coordinator instance directly.
"""

from typing import Any, Callable

from .events import CallbackEvent, CallbackType
from .unified_callbacks import TrulyUnifiedCallbacks


_callbacks = TrulyUnifiedCallbacks()


def register_callback(
    event: CallbackType,
    func: Callable[..., Any],
    *,
    component_id: str | None = None,
    **kwargs: Any,
) -> None:
    """Register ``func`` for ``event``.

    ``component_id`` is currently advisory and stored only for API compatibility
    with the legacy event bus based subscription system.
    """

    _callbacks.register_callback(event, func, **kwargs)


def unregister_callback(event: CallbackType, func: Callable[..., Any]) -> None:
    """Remove a previously registered callback."""

    _callbacks.unregister_callback(event, func)


def trigger_callback(event: CallbackType, *args: Any, **kwargs: Any) -> list[Any]:
    """Trigger callbacks registered for ``event``.

    The list of results returned by the callbacks is forwarded to the caller for
    introspection during testing.
    """

    return _callbacks.trigger_event(event, *args, **kwargs)


__all__ = ["register_callback", "unregister_callback", "trigger_callback", "_callbacks"]
