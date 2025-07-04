from __future__ import annotations

from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Any
import logging

from core.callback_manager import CallbackManager

logger = logging.getLogger(__name__)

class SecurityEvent(Enum):
    """Events emitted for security-related analytics."""

    THREAT_DETECTED = auto()
    ANALYSIS_COMPLETE = auto()
    ANOMALY_DETECTED = auto()
    SCORE_CALCULATED = auto()
    VALIDATION_FAILED = auto()

class SecurityCallbackController:
    """Manage callbacks for security events using :class:`CallbackManager`."""

    def __init__(self, manager: Optional[CallbackManager] = None) -> None:
        self._manager = manager or CallbackManager()
        self.history: List[tuple[SecurityEvent, Dict[str, Any]]] = []

    def register_callback(
        self, event: SecurityEvent, callback: Callable[[Dict[str, Any]], None], *, priority: int = 50
    ) -> None:
        self._manager.register_callback(event, callback, priority=priority)

    def unregister_callback(self, event: SecurityEvent, callback: Callable[[Dict[str, Any]], None]) -> bool:
        before = len(self._manager.get_callbacks(event))
        self._manager.unregister_callback(event, callback)
        after = len(self._manager.get_callbacks(event))
        return after < before

    def fire_event(self, event: SecurityEvent, data: Optional[Dict[str, Any]] = None) -> None:
        payload = data or {}
        self.history.append((event, payload))
        self._manager.trigger(event, payload)

    def clear_all_callbacks(self) -> None:
        self._manager = CallbackManager()
        self.history.clear()

def emit_security_event(event: SecurityEvent, data: Optional[Dict[str, Any]] = None) -> None:
    """Emit a security event using the global controller."""
    security_callback_controller.fire_event(event, data)


security_callback_controller = SecurityCallbackController()

__all__ = [
    "SecurityEvent",
    "SecurityCallbackController",
    "security_callback_controller",
    "emit_security_event",

]
