"""Unified callback utilities and event bus."""

from .event_bus import EventBus, EventPublisher

__all__ = [
    "EventBus",
    "EventPublisher",
    "Operation",
    "TrulyUnifiedCallbacks",
    "UnifiedCallbackManager",
]


def __getattr__(name: str):  # pragma: no cover - lazy loading
    if name in {"Operation", "TrulyUnifiedCallbacks", "UnifiedCallbackManager"}:
        from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import (
            Operation,
            TrulyUnifiedCallbacks,
        )

        globals().update(
            Operation=Operation,
            TrulyUnifiedCallbacks=TrulyUnifiedCallbacks,
            UnifiedCallbackManager=TrulyUnifiedCallbacks,
        )
        return globals()[name]
    raise AttributeError(name)
