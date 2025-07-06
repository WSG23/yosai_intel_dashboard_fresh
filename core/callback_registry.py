"""
Centralized Callback Registry for Dash Application
Manages all callbacks in a modular, organized way
"""

import logging
import time
from functools import wraps
from typing import Callable, List

from dash import no_update


def debounce(wait_ms: int = 300):
    """Return decorator to suppress rapid callback invocations."""

    def decorator(func: Callable):
        last_call = 0.0

        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_call
            now = time.monotonic() * 1000
            if now - last_call < wait_ms:
                return no_update
            last_call = now
            return func(*args, **kwargs)

        return wrapper

    return decorator

logger = logging.getLogger(__name__)


class CallbackRegistry:
    """Central registry for all application callbacks"""

    def __init__(self, app):
        self.app = app
        self.registered_callbacks = {}
        self.clientside_callbacks = {}

    # New unified decorator -----------------------------------------------
    def unified_callback(self, *args, **kwargs):
        """Return :class:`CallbackUnifier` bound to this registry."""
        from .plugins.callback_unifier import CallbackUnifier
        from .plugins.decorators import safe_callback

        return CallbackUnifier(self, safe_callback(self.app))(*args, **kwargs)

    def register_callback(
        self,
        outputs,
        inputs: List,
        states: List = None,
        prevent_initial_call: bool = True,
        callback_id: str = None,
        allow_duplicate: bool = False,
    ):
        """Decorator to register callbacks"""

        def decorator(func: Callable):
            if callback_id and callback_id in self.registered_callbacks:
                logger.warning(f"Callback {callback_id} already registered, skipping")
                return func

            try:
                # Handle allow_duplicate for Output objects
                if allow_duplicate and hasattr(outputs, "__iter__"):
                    for output in outputs if isinstance(outputs, list) else [outputs]:
                        if hasattr(output, "allow_duplicate"):
                            output.allow_duplicate = True

                @self.app.callback(
                    outputs,
                    inputs,
                    states or [],
                    prevent_initial_call=prevent_initial_call,
                )
                def wrapper(*args, **kwargs):
                    return func(*args, **kwargs)

                if callback_id:
                    self.registered_callbacks[callback_id] = wrapper
                    logger.debug(f"Registered callback: {callback_id}")

                return wrapper
            except Exception as e:
                logger.error(f"Failed to register callback {callback_id}: {e}")
                return func

        return decorator

    def register_clientside_callback(
        self,
        clientside_function: str,
        outputs,  # Don't specify type - can be single or list
        inputs: List,
        states: List = None,
        callback_id: str = None,
    ):
        """Register clientside callbacks"""
        if callback_id and callback_id in self.clientside_callbacks:
            logger.warning(
                f"Clientside callback {callback_id} already registered, skipping"
            )
            return

        try:
            self.app.clientside_callback(
                clientside_function, outputs, inputs, states or []  # Pass as-is
            )

            if callback_id:
                self.clientside_callbacks[callback_id] = True
                logger.debug(f"Registered clientside callback: {callback_id}")

        except Exception as e:
            logger.error(f"Failed to register clientside callback {callback_id}: {e}")


class ComponentCallbackManager:
    """Base class for component callback managers"""

    def __init__(self, callback_registry: CallbackRegistry):
        self.registry = callback_registry
        self.component_name = self.__class__.__name__.replace("CallbackManager", "")

    def register_all(self):
        """Register all callbacks for this component"""
        raise NotImplementedError("Subclasses must implement register_all")
