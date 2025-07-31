"""Simplified callback registry for unified callbacks."""
from __future__ import annotations

from typing import Any, Callable, Dict

from dash import Dash

class CallbackRegistry:
    """Minimal registry tracking registered callbacks."""

    def __init__(self, app: Dash | None = None) -> None:
        self.app = app
        self.registered_callbacks: Dict[str, Callable[..., Any]] = {}
        self.callback_sources: Dict[str, str] = {}

    def handle_register(self, outputs, inputs=None, states=None, **kwargs):
        """Decorator registering callback on the Dash app if available."""
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            callback_id = kwargs.get("callback_id", func.__name__)
            self.registered_callbacks[callback_id] = func
            if self.app is not None:
                self.app.callback(outputs, inputs, states, **kwargs)(func)
            return func

        return decorator

class ComponentCallbackManager:
    """Base class for components that register callbacks."""

    def __init__(self, registry: CallbackRegistry) -> None:
        self.registry = registry
        self.component_name = self.__class__.__name__.replace("CallbackManager", "")

    def register_all(self) -> None:  # pragma: no cover - interface
        raise NotImplementedError
