"""Compatibility wrapper for :mod:`core.callback_controller`."""

from core.callback_controller import (
    CallbackController,
    CallbackEvent,
    CallbackContext,
    callback_handler,
    TemporaryCallback,
    get_callback_controller,
    fire_event,
)

# Backwards compatibility aliases
SecurityEvent = CallbackEvent
emit_security_event = fire_event
callback_controller = CallbackController()
security_callback_controller = callback_controller

__all__ = [
    "CallbackEvent",
    "SecurityEvent",
    "CallbackContext",
    "CallbackController",
    "callback_handler",
    "TemporaryCallback",
    "get_callback_controller",
    "fire_event",
    "emit_security_event",
    "callback_controller",
    "security_callback_controller",
]
