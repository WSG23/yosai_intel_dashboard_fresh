"""Security event utilities."""

from typing import Any

from core.callback_events import CallbackEvent
from core.callbacks import UnifiedCallbackManager

SecurityEvent = CallbackEvent

# Default callback implementation now uses the unified manager
security_unified_callbacks: UnifiedCallbackManager = UnifiedCallbackManager()


def emit_security_event(event: SecurityEvent, data: dict | None = None) -> None:
    """Trigger *event* through ``security_unified_callbacks``."""
    if security_unified_callbacks:
        security_unified_callbacks.trigger_event(event, data)


__all__ = ["SecurityEvent", "emit_security_event", "security_unified_callbacks"]
