from __future__ import annotations

from enum import Enum, auto


class CallbackEvent(Enum):
    """Enumeration of application callback events."""

    BEFORE_REQUEST = auto()
    AFTER_REQUEST = auto()
    ANALYSIS_START = auto()
    ANALYSIS_PROGRESS = auto()
    ANALYSIS_COMPLETE = auto()
    ANALYSIS_ERROR = auto()
    DATA_PROCESSED = auto()
