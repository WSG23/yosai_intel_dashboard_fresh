"""Compatibility wrapper exposing security-specific callback names."""

from core.callback_events import CallbackEvent
from core.callback_manager import CallbackManager
from core.truly_unified_callbacks import TrulyUnifiedCallbacks

SecurityEvent = CallbackEvent
SecurityCallbackController = CallbackManager
security_callback_controller = CallbackManager()

def emit_security_event(event: SecurityEvent, data: dict | None = None) -> None:
    security_unified_callbacks.trigger(event, data)

__all__ = [
    "SecurityEvent",
    "SecurityCallbackController",
    "security_callback_controller",
    "emit_security_event",
]
