"""Consolidated callback controller for all system events."""

from __future__ import annotations

import asyncio
import logging
import threading
import weakref
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Protocol

from .base_model import BaseModel
from .callback_events import CallbackEvent
from .error_handling import ErrorCategory, ErrorSeverity, error_handler

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CallbackContext:
    """Immutable context data for callbacks."""

    event_type: CallbackEvent
    source_id: str
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:  # pragma: no cover - simple validation
        if not self.source_id:
            raise ValueError("source_id cannot be empty")


class CallbackProtocol(Protocol):
    """Protocol for callback functions."""

    def __call__(self, context: CallbackContext) -> None:  # pragma: no cover - protocol
        ...


class CallbackRegistry(BaseModel):
    """Thread-safe registry for managing callbacks."""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self._callbacks: Dict[CallbackEvent, List[CallbackProtocol]] = {}
        self._lock = threading.RLock()
        self._weak_refs: Dict[CallbackEvent, List[weakref.ref]] = {}

    def register(
        self,
        event: CallbackEvent,
        callback: CallbackProtocol,
        weak: bool = False,
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

    def unregister(self, event: CallbackEvent, callback: CallbackProtocol) -> bool:
        with self._lock:
            try:
                self._callbacks.get(event, []).remove(callback)
                return True
            except ValueError:
                return False

    def get_callbacks(self, event: CallbackEvent) -> List[CallbackProtocol]:
        with self._lock:
            callbacks: List[CallbackProtocol] = []
            callbacks.extend(self._callbacks.get(event, []))
            for weak_ref in self._weak_refs.get(event, []):
                cb = weak_ref()
                if cb is not None:
                    callbacks.append(cb)
            return callbacks

    def clear(self, event: Optional[CallbackEvent] = None) -> None:
        with self._lock:
            if event:
                self._callbacks.pop(event, None)
                self._weak_refs.pop(event, None)
            else:
                self._callbacks.clear()
                self._weak_refs.clear()


class CallbackController(BaseModel):
    """Main controller for managing all system callbacks."""

    _instance: Optional["CallbackController"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "CallbackController":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        if hasattr(self, "_initialized"):
            return

        self._registry = CallbackRegistry()
        self._error_handlers: List[Callable[[Exception, CallbackContext], None]] = []
        self._stats = {
            "events_fired": 0,
            "callbacks_executed": 0,
            "errors": 0,
        }
        self._initialized = True

    def register(
        self,
        event: CallbackEvent,
        callback: CallbackProtocol,
        weak: bool = False,
    ) -> None:
        """Register *callback* for *event*."""
        self._registry.register(event, callback, weak)
        logger.debug(f"Registered callback for {event.name}")

    # ------------------------------------------------------------------
    def handle_register(
        self,
        event: CallbackEvent,
        callback: CallbackProtocol,
        weak: bool = False,
    ) -> None:
        """Compatibility wrapper for :meth:`register`."""
        self.register(event, callback, weak)

    def unregister(self, event: CallbackEvent, callback: CallbackProtocol) -> bool:
        """Unregister *callback* from *event*."""
        success = self._registry.unregister(event, callback)
        if success:
            logger.debug(f"Unregistered callback for {event.name}")
        return success

    # ------------------------------------------------------------------
    def handle_unregister(
        self, event: CallbackEvent, callback: CallbackProtocol
    ) -> bool:
        """Compatibility wrapper for :meth:`unregister`."""
        return self.unregister(event, callback)

    # Backwards compatibility aliases
    register_handler = register
    unregister_handler = unregister

    async def emit(
        self,
        event: CallbackEvent,
        source_id: str,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        """Trigger callbacks for *event* asynchronously."""
        context = CallbackContext(
            event_type=event,
            source_id=source_id,
            timestamp=datetime.now(),
            data=data or {},
            metadata=metadata,
        )

        self._stats["events_fired"] += 1
        callbacks = self._registry.get_callbacks(event)

        if not callbacks:
            logger.debug(f"No callbacks registered for {event.name}")
            return []

        logger.debug(f"Firing {event.name} to {len(callbacks)} callbacks")

        results: List[Any] = []
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    result = await callback(context)
                else:
                    result = callback(context)
                self._stats["callbacks_executed"] += 1
                results.append(result)
            except Exception as exc:  # pragma: no cover - log and continue
                self._stats["errors"] += 1
                self._handle_callback_error(exc, context, callback)
                results.append(None)
        return results

    def fire_event(
        self,
        event: CallbackEvent,
        source_id: str,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Synchronous wrapper for :meth:`emit`."""
        asyncio.run(self.emit(event, source_id, data, metadata))

    def register_error_handler(
        self, handler: Callable[[Exception, CallbackContext], None]
    ) -> None:
        self._error_handlers.append(handler)

    def get_stats(self) -> Dict[str, Any]:
        return self._stats.copy()

    def reset_stats(self) -> None:
        self._stats = {"events_fired": 0, "callbacks_executed": 0, "errors": 0}

    def clear(self, event: Optional[CallbackEvent] = None) -> None:
        """Remove callbacks for *event* or all if None."""
        self._registry.clear(event)
        logger.info("Cleared all callbacks")

    # ------------------------------------------------------------------
    def clear_all_callbacks(self) -> None:
        self._registry.clear()
        logger.info("Cleared all callbacks")

    def _handle_callback_error(
        self,
        exc: Exception,
        context: CallbackContext,
        callback: CallbackProtocol,
    ) -> None:
        logger.error(
            f"Callback error for {context.event_type.name}: {exc}",
            exc_info=True,
        )
        # Consolidated error handling
        error_handler.handle_error(
            exc,
            category=ErrorCategory.USER_INPUT,
            severity=ErrorSeverity.HIGH,
            context={
                "event": context.event_type.name,
                "callback": getattr(callback, "__name__", str(callback)),
            },
        )
        for handler in self._error_handlers:
            try:
                handler(exc, context)
            except Exception as handler_exc:  # pragma: no cover - log
                logger.error(f"Error handler failed: {handler_exc}")


def callback_handler(event: CallbackEvent, weak: bool = False):
    """Decorator to register a function as a callback handler."""

    def decorator(func: CallbackProtocol) -> CallbackProtocol:
        controller = CallbackController()
        controller.register_handler(event, func, weak)
        return func

    return decorator


class TemporaryCallback:
    """Context manager for temporary callback registration."""

    def __init__(
        self,
        event: CallbackEvent,
        callback: CallbackProtocol,
        controller: Optional[CallbackController] = None,
    ) -> None:
        self.event = event
        self.callback = callback
        self.controller = controller or CallbackController()

    def __enter__(self) -> CallbackProtocol:
        self.controller.register_handler(self.event, self.callback)
        return self.callback

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.controller.unregister_handler(self.event, self.callback)


def get_callback_controller() -> CallbackController:
    """Get the global callback controller instance."""

    return CallbackController()


def fire_event(
    event: CallbackEvent,
    source_id: str,
    data: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    controller = CallbackController()
    controller.fire_event(event, source_id, data, metadata)


__all__ = [
    "CallbackEvent",
    "CallbackContext",
    "CallbackProtocol",
    "CallbackRegistry",
    "CallbackController",
    "callback_handler",
    "TemporaryCallback",
    "get_callback_controller",
    "fire_event",
]
