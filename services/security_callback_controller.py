"""Compatibility wrapper exposing security-specific callback names."""

from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from security.events import (
    SecurityEvent,
    emit_security_event,
    security_unified_callbacks,
)

SecurityCallbackController = TrulyUnifiedCallbacks
security_callback_controller = TrulyUnifiedCallbacks()

__all__ = [
    "SecurityEvent",
    "SecurityCallbackController",
    "security_callback_controller",
    "emit_security_event",
]
