"""Deprecated; use :mod:`shared.events.bus` instead."""

from warnings import warn

from shared.events.bus import EventBus, EventPublisher

warn(
    "yosai_intel_dashboard.src.core.callbacks.event_bus is deprecated; use shared.events.bus",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["EventBus", "EventPublisher"]
