"""Compatibility wrapper exposing security-specific callback names."""

from core.callbacks import UnifiedCallbackManager
from security.events import (
    SecurityEvent,
    emit_security_event,
    security_unified_callbacks,
)

SecurityCallbackController = UnifiedCallbackManager
security_callback_controller = UnifiedCallbackManager()

__all__ = [
    "SecurityEvent",
    "SecurityCallbackController",
    "security_callback_controller",
    "emit_security_event",
]
