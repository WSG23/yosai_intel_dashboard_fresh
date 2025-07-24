"""Core error handling primitives."""

import logging
from dataclasses import dataclass
from typing import Any, Optional

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
    ) -> YosaiException:
        """Create a :class:`YosaiException` for *exc* and log it."""

        self.log.exception("unhandled error", exc_info=exc)
        context = ErrorContext(exc, category, str(exc), details)
        return YosaiException(context.category, context.message, context.details)


__all__ = ["ErrorHandler", "ErrorContext"]
