from __future__ import annotations

from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Any
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class SecurityEvent(Enum):
    """Events emitted for security-related analytics."""

    THREAT_DETECTED = auto()
    ANALYSIS_COMPLETE = auto()
    ANOMALY_DETECTED = auto()
    SCORE_CALCULATED = auto()
    VALIDATION_FAILED = auto()

class SecurityCallbackController:
    """Manage callbacks for security events."""

    def __init__(self) -> None:
        self._callbacks: Dict[SecurityEvent, List[Callable[[Dict[str, Any]], None]]] = defaultdict(list)

    def register_callback(self, event: SecurityEvent, callback: Callable[[Dict[str, Any]], None]) -> None:
        self._callbacks[event].append(callback)

    def unregister_callback(self, event: SecurityEvent, callback: Callable[[Dict[str, Any]], None]) -> bool:
        try:
            self._callbacks[event].remove(callback)
            return True
        except (ValueError, KeyError):
            return False

    def fire_event(self, event: SecurityEvent, data: Optional[Dict[str, Any]] = None) -> None:
        for cb in list(self._callbacks.get(event, [])):
            try:
                cb(data or {})
            except Exception:  # pragma: no cover - log and continue
                logger.exception("Callback error for %s", event.name)

    def clear_all_callbacks(self) -> None:
        self._callbacks.clear()

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
