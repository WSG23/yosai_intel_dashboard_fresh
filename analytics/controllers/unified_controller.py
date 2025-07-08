from __future__ import annotations

"""Unified analytics controller with async callbacks and security checks."""

import logging
from typing import Any, Callable, Dict, List, Optional

from core.callback_events import CallbackEvent
from core.callback_manager import CallbackManager
from core.security_validator import SecurityValidator


class UnifiedAnalyticsController:
    """Manage analytics callbacks with optional security validation."""

    _EVENT_MAP: Dict[str, CallbackEvent] = {
        "on_analysis_start": CallbackEvent.ANALYSIS_START,
        "on_analysis_progress": CallbackEvent.ANALYSIS_PROGRESS,
        "on_analysis_complete": CallbackEvent.ANALYSIS_COMPLETE,
        "on_analysis_error": CallbackEvent.ANALYSIS_ERROR,
        "on_data_processed": CallbackEvent.DATA_PROCESSED,
    }

    def __init__(
        self,
        callback_manager: Optional[CallbackManager] = None,
        security_validator: Optional[SecurityValidator] = None,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self._manager = callback_manager or CallbackManager()
        self._validator = security_validator or SecurityValidator()

    # ------------------------------------------------------------------
    def handle_register(
        self,
        event: str,
        callback: Callable[..., Any],
        *,
        secure: bool = False,
        priority: int = 50,
    ) -> None:
        """Register a callback for an event."""
        if event not in self._EVENT_MAP:
            raise ValueError(f"Unknown event type: {event}")

        if secure:
            original = callback

            def wrapped(*args: Any, **kwargs: Any) -> Any:
                if args and isinstance(args[0], str):
                    result = self._validator.validate_input(args[0], "input")
                    if not result["valid"]:
                        self.logger.error(
                            "Security validation failed: %s", result["issues"]
                        )
                        return None
                    args = (result["sanitized"],) + args[1:]
                return original(*args, **kwargs)

            callback = wrapped

        self._manager.register_handler(
            self._EVENT_MAP[event], callback, priority=priority
        )

    def register_security_callbacks(self, callback_dict: Dict[str, callable]):
        """Consolidated callback registration for security analysis"""
        for event_name, callback_func in callback_dict.items():
            self.register_handler(event_name, callback_func, secure=True)

    # ------------------------------------------------------------------
    def handle_unregister(self, event: str, callback: Callable[..., Any]) -> None:
        """Remove a previously registered callback."""
        if event not in self._EVENT_MAP:
            return
        self._manager.unregister_handler(self._EVENT_MAP[event], callback)

    # ------------------------------------------------------------------
    def trigger(self, event: str, *args: Any, **kwargs: Any) -> List[Any]:
        """Synchronously trigger callbacks for an event."""
        if event not in self._EVENT_MAP:
            return []
        return self._manager.trigger(self._EVENT_MAP[event], *args, **kwargs)

    # ------------------------------------------------------------------
    async def trigger_async(self, event: str, *args: Any, **kwargs: Any) -> List[Any]:
        """Asynchronously trigger callbacks for an event."""
        if event not in self._EVENT_MAP:
            return []
        return await self._manager.trigger_async(
            self._EVENT_MAP[event], *args, **kwargs
        )
