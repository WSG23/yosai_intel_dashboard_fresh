"""Security event utilities."""
from typing import Any
from core.callback_events import CallbackEvent

SecurityEvent = CallbackEvent

# Default callback implementation
class DefaultSecurityCallbacks:
    """Default security callback handler"""
    def trigger(self, event, data=None):
        """Default trigger - just log for now"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Security event: {event}, data: {data}")

# Instance of callback handler - can be overridden at runtime
security_unified_callbacks = DefaultSecurityCallbacks()

def emit_security_event(event: SecurityEvent, data: dict | None = None) -> None:
    """Trigger *event* through ``security_unified_callbacks``."""
    if security_unified_callbacks:
        security_unified_callbacks.trigger(event, data)

__all__ = ["SecurityEvent", "emit_security_event", "security_unified_callbacks"]
