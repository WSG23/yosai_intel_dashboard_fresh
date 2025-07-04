"""Migration helpers for the new callback system."""

from __future__ import annotations

from dash import Dash

from .callback_manager import CallbackManager
from .callback_events import CallbackEvent
from .truly_unified_callbacks import TrulyUnifiedCallbacks


class UnifiedCallbackCoordinatorWrapper(TrulyUnifiedCallbacks):
    """Wrapper exposing a callback manager for backward compatibility."""

    def __init__(self, app: Dash, callback_manager: CallbackManager) -> None:
        super().__init__(app)
        self.callback_manager = callback_manager

    def register_event(self, event: CallbackEvent, func, *, priority: int = 50) -> None:
        """Register an event callback through :class:`CallbackManager`."""
        self.callback_manager.register_callback(event, func, priority=priority)
