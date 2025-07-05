"""Deprecated wrapper around the unified callback controller.

This module provides backward compatible access to the callback controller
APIs now located in :mod:`core.callback_controller` and
:mod:`security_callback_controller`.
"""

from core.callback_controller import (
    CallbackEvent,
    CallbackContext,
    CallbackProtocol,
    CallbackRegistry,
    CallbackController,

    callback_handler,
    TemporaryCallback,
    get_callback_controller,
    fire_event,
)
from security_callback_controller import (
    SecurityEvent,
    SecurityCallbackController,
    security_callback_controller as _security_callback_controller,
    emit_security_event,
)

# Global instances preserved for compatibility
callback_controller = CallbackController()
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
