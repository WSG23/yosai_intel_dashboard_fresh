"""Simplified callback registry for unified callbacks."""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable

from dash import Dash
from dash.dependencies import Input, Output, State


class CallbackRegistry:
    """Minimal registry tracking registered callbacks."""

    def __init__(self, app: Dash | None = None) -> None:
        self.app = app
        self.registered_callbacks: Dict[str, Callable[..., Any]] = {}
        self.callback_sources: Dict[str, str] = {}

    def handle_register(
        self,
        outputs: Output | Iterable[Output],
        inputs: Iterable[Input] | Input | None = None,
        states: Iterable[State] | State | None = None,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Return a decorator registering a Dash callback if the app exists.

        Parameters
        ----------
        outputs:
            A Dash ``Output`` or iterable of ``Output`` objects to be produced by
            the callback.
        inputs:
            Optional ``Input`` or iterable of ``Input`` objects providing
            callback arguments.
        states:
            Optional ``State`` or iterable of ``State`` objects available to the
            callback without triggering it.

        Returns
        -------
        Callable[[Callable[..., Any]], Callable[..., Any]]
            A decorator that registers the provided function as a callback.
        """

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
