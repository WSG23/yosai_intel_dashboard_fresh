#!/usr/bin/env python3
"""Simple Callback Manager for Dash applications."""
from __future__ import annotations

from dash import Dash
from typing import Callable, Any

class CallbackManager:
    """Register Dash callbacks and prevent duplicate IDs."""

    def __init__(self, app: Dash) -> None:
        self.app = app
        self._registered_ids: set[str] = set()

    @property
    def registered_ids(self) -> set[str]:
        """Return a copy of registered callback IDs."""
        return set(self._registered_ids)

    def callback(
        self,
        *args: Any,
        callback_id: str,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Wrap ``Dash.callback`` and track callback IDs.

        Parameters
        ----------
        callback_id:
            Unique identifier for the callback. Attempting to register a
            duplicate ID will raise ``ValueError``.
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            if callback_id in self._registered_ids:
                raise ValueError(f"Callback ID '{callback_id}' already registered")
            wrapped = self.app.callback(*args, **kwargs)(func)
            self._registered_ids.add(callback_id)
            return wrapped

        return decorator

