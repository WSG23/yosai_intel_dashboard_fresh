from __future__ import annotations

from enum import Enum, auto


class CallbackEvent(Enum):
    """Enumeration of application callback events."""

    BEFORE_REQUEST = auto()
    AFTER_REQUEST = auto()
    FILE_UPLOAD_START = auto()
    FILE_UPLOAD_COMPLETE = auto()
    FILE_UPLOAD_ERROR = auto()
    FILE_PROCESSING_START = auto()
    FILE_PROCESSING_COMPLETE = auto()
    FILE_PROCESSING_ERROR = auto()
    ANALYSIS_START = auto()
    ANALYSIS_PROGRESS = auto()
    ANALYSIS_COMPLETE = auto()
    ANALYSIS_ERROR = auto()
    DATA_PROCESSED = auto()
    DATA_QUALITY_CHECK = auto()
    DATA_QUALITY_ISSUE = auto()
    USER_ACTION = auto()
    UI_UPDATE = auto()
    SYSTEM_ERROR = auto()
    SYSTEM_WARNING = auto()
    THREAT_DETECTED = auto()
    ANOMALY_DETECTED = auto()
    SCORE_CALCULATED = auto()
    VALIDATION_FAILED = auto()


__all__ = ["CallbackEvent"]
