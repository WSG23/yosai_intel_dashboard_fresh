from __future__ import annotations

"""Backwards compatible wrapper around :class:`TrulyUnifiedCallbacks`."""

import logging
from typing import Any, Callable, Iterable, Optional

from dash import Dash
from dash.dependencies import Input, State

from .callback_events import CallbackEvent
from .callback_manager import CallbackManager
from .security_validator import SecurityValidator
from .truly_unified_callbacks import TrulyUnifiedCallbacks

logger = logging.getLogger(__name__)


class MasterCallbackSystem(TrulyUnifiedCallbacks):
    """Lightweight wrapper preserved for legacy imports."""

    def __init__(
        self,
        app: Dash,
        *,
        security_validator: Optional[SecurityValidator] = None,
    ) -> None:
        super().__init__(app)

        self.callback_manager = CallbackManager()
        self.security = security_validator or SecurityValidator()

    # ------------------------------------------------------------------
    def handle_register_event(
        self,
        event: CallbackEvent,
        func: Callable[..., Any],
        *,
        priority: int = 50,
        secure: bool = False,
    ) -> None:
        """Register an event callback with optional security check."""

        if secure:
            original = func

            def wrapped(*args: Any, **kwargs: Any) -> Any:
                if args and isinstance(args[0], str):
                    result = self.security.validate_input(args[0], "input")
                    if not result["valid"]:
                        logger.error("Security validation failed: %s", result["issues"])
                        return None
                    args = (result["sanitized"],) + args[1:]
                return original(*args, **kwargs)

            func = wrapped

        self.callback_manager.register_handler(event, func, priority=priority)

    # ------------------------------------------------------------------
    def trigger_event(self, event: CallbackEvent, *args: Any, **kwargs: Any):
        """Synchronously trigger callbacks for *event*."""
        return self.callback_manager.trigger(event, *args, **kwargs)

    # ------------------------------------------------------------------
    async def trigger_event_async(
        self, event: CallbackEvent, *args: Any, **kwargs: Any
    ):
        """Asynchronously trigger callbacks for *event*."""
        return await self.callback_manager.trigger_async(event, *args, **kwargs)

    # ------------------------------------------------------------------
    def handle_register_dash(
        self,
        outputs: Any,
        inputs: Iterable[Input] | Input | None = None,
        states: Iterable[State] | State | None = None,
        *,
        callback_id: str,
        component_name: str,
        allow_duplicate: bool = False,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Wrap ``Dash.callback`` and track registrations."""
        return self.register_handler(
            outputs,
            inputs,
            states,
            callback_id=callback_id,
            component_name=component_name,
            allow_duplicate=allow_duplicate,
            **kwargs,
        )

    # ------------------------------------------------------------------
    def get_callback_conflicts(self):
        """Return mapping of output identifiers to conflicting callback IDs."""
        return super().get_callback_conflicts()

    # ------------------------------------------------------------------
    def print_callback_summary(self) -> None:  # pragma: no cover - passthrough
        super().print_callback_summary()

    # ------------------------------------------------------------------
    def get_metrics(self, event: CallbackEvent):
        """Return execution metrics for *event*."""
        return self.callback_manager.get_metrics(event)


__all__ = ["MasterCallbackSystem"]
