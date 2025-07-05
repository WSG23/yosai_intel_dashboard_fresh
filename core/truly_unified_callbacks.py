from __future__ import annotations

"""Truly unified callback system combining registry and coordinator."""

from typing import Any, TYPE_CHECKING
from dash import Dash

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from .plugins.callback_unifier import CallbackUnifier


class TrulyUnifiedCallbacks:
    """Single callback system replacing all others."""

    def __init__(self, app: Dash) -> None:
        self.app = app
        self.coordinator = None  # backwards compat
        self.registry = None

    def callback(self, *args: Any, **kwargs: Any):
        """Unified callback decorator."""
        from .plugins.callback_unifier import CallbackUnifier

        return CallbackUnifier(self)(*args, **kwargs)

    unified_callback = callback

    # Basic pass-through for Dash.callback ---------------------------------
    def register_callback(self, outputs, inputs=None, states=None, **kwargs):
        if inputs is None:
            inputs = []
        if states is None:
            states = []
        return self.app.callback(outputs, inputs, states, **kwargs)
