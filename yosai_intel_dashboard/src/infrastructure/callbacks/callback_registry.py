"""Simplified callback registry for unified callbacks."""

from __future__ import annotations

import logging
from collections import defaultdict
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, DefaultDict, Dict, Iterable, List, Type

from dash import Dash
from dash.dependencies import Input, Output, State

from src.common.meta import AutoRegister

if TYPE_CHECKING:  # pragma: no cover
    from .unified_callbacks import CallbackHandler
else:  # pragma: no cover - fallback to generic callable at runtime
    CallbackHandler = Callable[..., Any]


class CallbackRegistry:
    """Minimal registry tracking registered callbacks."""

    def __init__(self, app: Dash | None = None) -> None:
        self.app = app
        self.registered_callbacks: Dict[str, CallbackHandler] = {}
        self.callback_sources: Dict[str, str] = {}

    def handle_register(
        self,
        outputs: Output | Iterable[Output],
        inputs: Iterable[Input] | Input | None = None,
        states: Iterable[State] | State | None = None,
        **kwargs: Any,
    ) -> Callable[[CallbackHandler], CallbackHandler]:
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
        Callable[[CallbackHandler], CallbackHandler]
            A decorator that registers the provided function as a callback.
        """

        def decorator(func: CallbackHandler) -> CallbackHandler:
            callback_id = kwargs.get("callback_id", func.__name__)
            self.registered_callbacks[callback_id] = func
            if self.app is not None:
                self.app.callback(outputs, inputs, states, **kwargs)(func)
            return func

        return decorator

    # ------------------------------------------------------------------
    def register_callback(
        self,
        outputs: Output | Iterable[Output],
        inputs: Iterable[Input] | Input | None = None,
        states: Iterable[State] | State | None = None,
        **kwargs: Any,
    ) -> Callable[[CallbackHandler], CallbackHandler]:
        """Alias of :meth:`handle_register` for API consistency."""

        return self.handle_register(outputs, inputs, states, **kwargs)

    # ``register_handler`` remains the canonical internal name used by
    # :class:`CallbackUnifier` and other helpers.  Providing it here keeps the
    # interface aligned with :class:`TrulyUnifiedCallbacks` and avoids the
    # proliferation of differing registration patterns across the codebase.
    register_handler = register_callback


class ComponentCallbackManager(metaclass=AutoRegister):
    """Base class for components that register callbacks."""

    REGISTRY: Dict[str, Type["ComponentCallbackManager"]] = {}

    def __init__(self, registry: CallbackRegistry) -> None:
        self.registry = registry
        self.component_name = self.__class__.__name__.replace("CallbackManager", "")

    def register_all(
        self,
    ) -> Dict[str, CallbackHandler]:  # pragma: no cover - interface
        raise NotImplementedError


logger = logging.getLogger(__name__)


class CallbackType(str, Enum):
    """Enumeration of supported callback types."""

    EVENT = "event"
    DASH = "dash"
    OPERATION = "operation"
    GENERAL = "general"


class UnifiedCallbackRegistry:
    """Registry storing callbacks globally and per component."""

    def __init__(self) -> None:
        self._callbacks: DefaultDict[CallbackType, List[CallbackHandler]] = defaultdict(
            list
        )
        self._component_callbacks: DefaultDict[
            str, DefaultDict[CallbackType, List[CallbackHandler]]
        ] = defaultdict(lambda: defaultdict(list))

    # ------------------------------------------------------------------
    def register_callback(
        self,
        callback_type: CallbackType,
        func: CallbackHandler,
        *,
        component: str | None = None,
    ) -> None:
        """Register ``func`` for ``callback_type`` optionally scoped to ``component``."""

        self._callbacks[callback_type].append(func)
        if component is not None:
            self._component_callbacks[component][callback_type].append(func)

    # ------------------------------------------------------------------
    def trigger_callback(
        self,
        callback_type: CallbackType,
        *args: Any,
        component: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Invoke callbacks of ``callback_type`` with provided arguments.

        If ``component`` is provided, only callbacks registered to that component
        are executed, in addition to any global callbacks of the same type.
        Exceptions raised by callbacks are logged but do not interrupt other
        callbacks.
        """

        callbacks: List[CallbackHandler] = list(self._callbacks.get(callback_type, []))
        if component is not None:
            callbacks.extend(
                self._component_callbacks.get(component, {}).get(callback_type, [])
            )

        for cb in callbacks:
            try:
                cb(*args, **kwargs)
            except Exception:  # pragma: no cover - logging side effect
                logger.exception(
                    "Error in callback %s for %s",
                    getattr(cb, "__name__", cb),
                    callback_type,
                )

    # ------------------------------------------------------------------
    def unregister_component(self, component: str) -> None:
        """Remove all callbacks registered by ``component``."""

        comp_callbacks = self._component_callbacks.pop(component, {})
        for ctype, funcs in comp_callbacks.items():
            global_list = self._callbacks.get(ctype)
            if not global_list:
                continue
            for func in funcs:
                try:
                    global_list.remove(func)
                except ValueError:
                    pass


__all__ = [
    "CallbackRegistry",
    "ComponentCallbackManager",
    "CallbackType",
    "UnifiedCallbackRegistry",
]
