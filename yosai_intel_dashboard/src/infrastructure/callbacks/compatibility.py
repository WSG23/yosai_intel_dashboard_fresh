"""Compatibility layer for legacy callback imports."""

from .events import CallbackEvent
from .unified_callbacks import TrulyUnifiedCallbacks

__all__ = ["TrulyUnifiedCallbacks", "CallbackEvent"]
