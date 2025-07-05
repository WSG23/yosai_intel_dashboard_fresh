"""Deprecated wrapper around the unified callback controller.

This module provides backward compatible access to the callback controller
APIs now located in :mod:`core.callback_manager` and
:mod:`security_callback_controller`.
"""

from core.callback_manager import CallbackManager as CallbackController
from core.callback_events import CallbackEvent
from core.callback_manager import CallbackManager
from core.callback_manager import CallbackManager as CallbackRegistry  # compat
CallbackContext = object
CallbackProtocol = object

callback_controller = CallbackController()

def callback_handler(event: CallbackEvent):
    def decorator(func):
        callback_controller.register_callback(event, func)
        return func
    return decorator

class TemporaryCallback:
    def __init__(self, event: CallbackEvent, cb, controller: CallbackController | None = None):
        self.event = event
        self.cb = cb
        self.controller = controller or callback_controller

    def __enter__(self):
        self.controller.register_callback(self.event, self.cb)
        return self.cb

    def __exit__(self, exc_type, exc, tb):
        self.controller.unregister_callback(self.event, self.cb)

def get_callback_controller() -> CallbackController:
    return callback_controller

def fire_event(event: CallbackEvent, *args, **kwargs) -> None:
    callback_controller.trigger(event, *args, **kwargs)
from security_callback_controller import (
    SecurityEvent,
    SecurityCallbackController,
    security_callback_controller as _security_callback_controller,
    emit_security_event,
)

# Global instances preserved for compatibility
security_callback_controller = _security_callback_controller


__all__ = [
    "CallbackEvent",
    "SecurityEvent",
    "CallbackContext",
    "CallbackController",
    "SecurityCallbackController",
    "callback_handler",
    "TemporaryCallback",
    "get_callback_controller",
    "fire_event",
    "emit_security_event",
    "callback_controller",
    "security_callback_controller",
]
