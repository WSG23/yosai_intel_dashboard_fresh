"""Security callback management with Unicode sanitization."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional

from unicode_handler import UnicodeProcessor

logger = logging.getLogger(__name__)


class SecurityEventType(Enum):
    """Types of security events."""

    ALERT = auto()
    INFO = auto()
    ERROR = auto()


@dataclass
class SecurityEvent:
    """Data structure representing a security event."""

    event_type: SecurityEventType
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)


class UnicodeSecurityHandler:
    """Utility to sanitize event data using :mod:`unicode_handler`."""

    @staticmethod
    def sanitize_text(text: Any) -> str:
        return UnicodeProcessor.safe_encode_text(text)

    @classmethod
    def sanitize_event_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        cleaned: Dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, dict):
                cleaned[key] = cls.sanitize_event_data(value)
            elif isinstance(value, list):
                cleaned[key] = [
                    (
                        cls.sanitize_event_data(v)
                        if isinstance(v, dict)
                        else cls.sanitize_text(v)
                    )
                    for v in value
                ]
            else:
                cleaned[key] = cls.sanitize_text(value)
        return cleaned


class SecurityCallbackController:
    """Singleton controller managing security callbacks and history."""

    _instance: Optional["SecurityCallbackController"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "SecurityCallbackController":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return
        self._callbacks: Dict[
            SecurityEventType, List[Callable[[SecurityEvent], None]]
        ] = {}
        self._history: List[SecurityEvent] = []
        self._initialized = True

    # ------------------------------------------------------------------
    def register_callback(
        self, event: SecurityEventType, callback: Callable[[SecurityEvent], None]
    ) -> None:
        self._callbacks.setdefault(event, []).append(callback)

    def unregister_callback(
        self, event: SecurityEventType, callback: Callable[[SecurityEvent], None]
    ) -> bool:
        try:
            self._callbacks.get(event, []).remove(callback)
            return True
        except (ValueError, KeyError):
            return False

    # ------------------------------------------------------------------
    def emit(
        self, event: SecurityEventType, data: Optional[Dict[str, Any]] = None
    ) -> None:
        sanitized = UnicodeSecurityHandler.sanitize_event_data(data or {})
        record = SecurityEvent(event, sanitized)
        self._history.append(record)

        callbacks = list(self._callbacks.get(event, []))
        for cb in callbacks:
            try:
                cb(record)
            except Exception:  # pragma: no cover - log and continue
                logger.exception("Security callback error")

    def get_history(self) -> List[SecurityEvent]:
        return list(self._history)


# ---------------------------------------------------------------------------
# Helper functions

_callback_controller: Optional[SecurityCallbackController] = None


def create_security_callback_controller() -> SecurityCallbackController:
    """Create or return the global :class:`SecurityCallbackController`."""

    global _callback_controller
    if _callback_controller is None:
        _callback_controller = SecurityCallbackController()
    return _callback_controller


def emit_security_event(
    event: SecurityEventType, data: Optional[Dict[str, Any]] = None
) -> None:
    """Emit a security event via the global controller."""

    controller = create_security_callback_controller()
    controller.emit(event, data)


class SecurityModuleIntegration:
    """Integration helpers for registering default security callbacks."""

    def __init__(self, controller: Optional[SecurityCallbackController] = None) -> None:
        self.controller = controller or create_security_callback_controller()

    def register_default_callbacks(self) -> None:
        self.controller.register_callback(SecurityEventType.ALERT, self._log_alert)
        self.controller.register_callback(SecurityEventType.ERROR, self._log_error)

    @staticmethod
    def _log_alert(event: SecurityEvent) -> None:
        logger.info("Security alert: %s", event.data)

    @staticmethod
    def _log_error(event: SecurityEvent) -> None:
        logger.error("Security error: %s", event.data)


__all__ = [
    "SecurityEventType",
    "SecurityEvent",
    "SecurityCallbackController",
    "create_security_callback_controller",
    "emit_security_event",
    "UnicodeSecurityHandler",
    "SecurityModuleIntegration",
]
