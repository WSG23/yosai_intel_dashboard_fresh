from __future__ import annotations

"""Callback manager for analytics related Dash callbacks."""

from core.callback_registry import CallbackRegistry, ComponentCallbackManager
from pages.deep_analytics.callbacks import register_callbacks as _register


class AnalyticsCallbacks(ComponentCallbackManager):
    """Register deep analytics callbacks."""

    def register_all(self) -> None:
        _register(self.registry)


__all__ = ["AnalyticsCallbacks"]
