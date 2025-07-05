"""Compatibility wrapper for :mod:`core.callback_controller` with security naming."""

from core.callback_controller import (
    CallbackController,
    CallbackEvent,
    fire_event,
)

SecurityEvent = CallbackEvent
SecurityCallbackController = CallbackController
security_callback_controller = CallbackController()
emit_security_event = fire_event

__all__ = [
    "SecurityEvent",
    "SecurityCallbackController",
    "security_callback_controller",
    "emit_security_event",
]
