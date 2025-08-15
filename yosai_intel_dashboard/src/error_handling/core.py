"""Core error handling primitives."""

import logging
from dataclasses import dataclass
from typing import Any, Optional

# ``record_error`` depends on optional monitoring libraries. During tests those
# dependencies may not be installed, so fall back to a no-op implementation.
try:
    from yosai_intel_dashboard.src.infrastructure.monitoring.error_budget import (
        record_error,
    )
except Exception:  # pragma: no cover - best effort when monitoring is absent
    def record_error(service: str) -> None:  # type: ignore[no-redef]
        """Fallback no-op used when monitoring dependencies are missing."""
        return None

from .exceptions import ErrorCategory, YosaiException


@dataclass
class ErrorContext:
    """Runtime context captured when handling an exception."""

    exception: Exception
    category: ErrorCategory
    message: str
    details: Optional[Any] = None


class ErrorHandler:
    """Convert exceptions to :class:`YosaiException` objects."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.log = logger or logging.getLogger(__name__)

    def handle(
        self,
        exc: Exception,
        category: ErrorCategory = ErrorCategory.INTERNAL,
        details: Optional[Any] = None,
        service: str = "unknown",
    ) -> YosaiException:
        """Create a :class:`YosaiException` for *exc* and log it."""

        self.log.exception("unhandled error", exc_info=exc)
        record_error(service)
        context = ErrorContext(exc, category, str(exc), details)
        return YosaiException(context.category, context.message, context.details)


__all__ = ["ErrorHandler", "ErrorContext"]
