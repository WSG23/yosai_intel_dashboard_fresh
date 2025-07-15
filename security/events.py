"""Security event utilities."""

from typing import Any

from core.callback_events import CallbackEvent

SecurityEvent = CallbackEvent

# Instance of ``TrulyUnifiedCallbacks`` assigned at runtime.
security_unified_callbacks: Any


def emit_security_event(event: SecurityEvent, data: dict | None = None) -> None:
    """Trigger *event* through ``security_unified_callbacks``."""
    security_unified_callbacks.trigger(event, data)


__all__ = ["SecurityEvent", "emit_security_event", "security_unified_callbacks"]
