"""Compatibility wrapper exposing security-specific callback names."""

from core.callback_controller import CallbackEvent
from core.callback_manager import CallbackManager

SecurityEvent = CallbackEvent
SecurityCallbackController = CallbackManager
security_callback_controller = CallbackManager()

def emit_security_event(event: SecurityEvent, data: dict | None = None) -> None:
    security_callback_controller.trigger(event, data)

__all__ = [
    "SecurityEvent",
    "SecurityCallbackController",
    "security_callback_controller",
    "emit_security_event",
]
