from enum import Enum

class EventName(str, Enum):
    """Canonical event names used across the application."""

    METRICS_UPDATE = "metrics_update"
    ANALYTICS_UPDATE = "analytics_update"

__all__ = ["EventName"]
