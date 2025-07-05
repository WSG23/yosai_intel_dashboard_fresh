from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Protocol
import weakref

logger = logging.getLogger(__name__)


class BaseEvent(Enum):
    """Base event type for callbacks."""


class CallbackEvent(BaseEvent):
    """Standard events for data processing and UI."""

    FILE_UPLOAD_START = auto()
    FILE_UPLOAD_COMPLETE = auto()
    FILE_UPLOAD_ERROR = auto()
    FILE_PROCESSING_START = auto()
    FILE_PROCESSING_COMPLETE = auto()
    FILE_PROCESSING_ERROR = auto()
    ANALYSIS_START = auto()
    ANALYSIS_COMPLETE = auto()
    ANALYSIS_ERROR = auto()
    ANALYSIS_PROGRESS = auto()
    DATA_QUALITY_CHECK = auto()
    DATA_QUALITY_ISSUE = auto()
    USER_ACTION = auto()
    UI_UPDATE = auto()
    SYSTEM_ERROR = auto()
    SYSTEM_WARNING = auto()


class SecurityEvent(BaseEvent):
    """Events emitted for security-related analytics."""

    THREAT_DETECTED = auto()
    ANALYSIS_COMPLETE = auto()
    ANOMALY_DETECTED = auto()
    SCORE_CALCULATED = auto()
    VALIDATION_FAILED = auto()


@dataclass(frozen=True)
class CallbackContext:
    """Context data provided to callbacks."""

    event_type: BaseEvent
    source_id: str
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id cannot be empty")


class CallbackProtocol(Protocol):
    """Protocol for callback functions."""

    def __call__(self, context: CallbackContext) -> None:
        ...


class CallbackRegistry:
    """Thread-safe registry for managing callbacks."""

    def __init__(self) -> None:
        self._callbacks: Dict[BaseEvent, List[CallbackProtocol]] = {}
        self._lock = threading.RLock()
        self._weak_refs: Dict[BaseEvent, List[weakref.ref]] = {}

    def register(
        self, event: BaseEvent, callback: CallbackProtocol, weak: bool = False
    ) -> None:
        with self._lock:
            if event not in self._callbacks:
                self._callbacks[event] = []
                self._weak_refs[event] = []

            if weak:
                def cleanup(ref: weakref.ref) -> None:
                    with self._lock:
                        try:
                            self._weak_refs[event].remove(ref)
                        except ValueError:
                            pass

                weak_ref = weakref.ref(callback, cleanup)
                self._weak_refs[event].append(weak_ref)
            else:
                self._callbacks[event].append(callback)

    def unregister(self, event: BaseEvent, callback: CallbackProtocol) -> bool:
        with self._lock:
            try:
                self._callbacks.get(event, []).remove(callback)
                return True
            except ValueError:
                return False

    def get_callbacks(self, event: BaseEvent) -> List[CallbackProtocol]:
        with self._lock:
            callbacks: List[CallbackProtocol] = []
            callbacks.extend(self._callbacks.get(event, []))
            for weak_ref in self._weak_refs.get(event, []):
                cb = weak_ref()
                if cb is not None:
                    callbacks.append(cb)
            return callbacks

    def clear(self, event: Optional[BaseEvent] = None) -> None:
        with self._lock:
            if event:
                self._callbacks.pop(event, None)
                self._weak_refs.pop(event, None)
            else:
                self._callbacks.clear()
                self._weak_refs.clear()


class CallbackController:
    """Singleton controller managing all callbacks."""

    _instance: Optional["CallbackController"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "CallbackController":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return

        self._registry = CallbackRegistry()
        self._error_handlers: List[Callable[[Exception, CallbackContext], None]] = []
        self._stats = {
            "events_fired": 0,
            "callbacks_executed": 0,
            "errors": 0,
        }
        self.history: List[tuple[BaseEvent, Dict[str, Any]]] = []
        self._initialized = True

    def register_callback(
        self, event: BaseEvent, callback: CallbackProtocol, weak: bool = False
    ) -> None:
        self._registry.register(event, callback, weak)
        logger.debug("Registered callback for %s", event.name)

    def unregister_callback(self, event: BaseEvent, callback: CallbackProtocol) -> bool:
        success = self._registry.unregister(event, callback)
        if success:
            logger.debug("Unregistered callback for %s", event.name)
        return success

    def fire_event(
        self,
        event: BaseEvent,
        source_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        src = source_id or event.__class__.__name__
        context = CallbackContext(
            event_type=event,
            source_id=src,
            timestamp=datetime.now(),
            data=data or {},
            metadata=metadata,
        )

        self.history.append((event, data or {}))
        self._stats["events_fired"] += 1
        callbacks = self._registry.get_callbacks(event)

        if not callbacks:
            logger.debug("No callbacks registered for %s", event.name)
            return

        logger.debug("Firing %s to %d callbacks", event.name, len(callbacks))

        for callback in callbacks:
            try:
                callback(context)
                self._stats["callbacks_executed"] += 1
            except Exception as exc:  # pragma: no cover - log and continue
                self._stats["errors"] += 1
                self._handle_callback_error(exc, context, callback)

    def register_error_handler(self, handler: Callable[[Exception, CallbackContext], None]) -> None:
        self._error_handlers.append(handler)

    def get_stats(self) -> Dict[str, Any]:
        return self._stats.copy()

    def reset_stats(self) -> None:
        self._stats = {"events_fired": 0, "callbacks_executed": 0, "errors": 0}

    def clear_all_callbacks(self) -> None:
        self._registry.clear()
        self.history.clear()
        logger.info("Cleared all callbacks")

    def _handle_callback_error(
        self,
        exc: Exception,
        context: CallbackContext,
        callback: CallbackProtocol,
    ) -> None:
        logger.error("Callback error for %s: %s", context.event_type.name, exc, exc_info=True)
        for handler in self._error_handlers:
            try:
                handler(exc, context)
            except Exception as handler_exc:  # pragma: no cover - log
                logger.error("Error handler failed: %s", handler_exc)


def callback_handler(event: BaseEvent, weak: bool = False):
    """Decorator to register a function as a callback handler."""

    def decorator(func: CallbackProtocol) -> CallbackProtocol:
        controller = CallbackController()
        controller.register_callback(event, func, weak)
        return func

    return decorator


class TemporaryCallback:
    """Context manager for temporary callback registration."""

    def __init__(
        self,
        event: BaseEvent,
        callback: CallbackProtocol,
        controller: Optional[CallbackController] = None,
    ) -> None:
        self.event = event
        self.callback = callback
        self.controller = controller or CallbackController()

    def __enter__(self) -> CallbackProtocol:
        self.controller.register_callback(self.event, self.callback)
        return self.callback

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.controller.unregister_callback(self.event, self.callback)


def get_callback_controller() -> CallbackController:
    """Return the global callback controller instance."""

    return CallbackController()


def fire_event(
    event: BaseEvent,
    source_id: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    controller = CallbackController()
    controller.fire_event(event, source_id, data, metadata)


def emit_security_event(event: SecurityEvent, data: Optional[Dict[str, Any]] = None) -> None:
    """Backward compatible helper for security analytics modules."""
    fire_event(event, "security", data)


# Global instance for convenience
callback_controller = CallbackController()
security_callback_controller = callback_controller


__all__ = [
    "CallbackEvent",
    "SecurityEvent",
    "CallbackContext",
    "CallbackProtocol",
    "CallbackRegistry",
    "CallbackController",
    "callback_handler",
    "TemporaryCallback",
    "get_callback_controller",
    "fire_event",
    "emit_security_event",
    "callback_controller",
    "security_callback_controller",
]
