"""Compatibility wrapper exposing security-specific callback names."""

from analytics_core.callbacks.unified_callback_manager import CallbackManager
from security.events import (
    SecurityEvent,
    emit_security_event,
    security_unified_callbacks,
)

SecurityCallbackController = CallbackManager
security_callback_controller = CallbackManager()

__all__ = [
    "SecurityEvent",
    "SecurityCallbackController",
    "security_callback_controller",
    "emit_security_event",
]
