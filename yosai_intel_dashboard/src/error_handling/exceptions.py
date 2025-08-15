"""Application specific exceptions using the standard error contract."""

from enum import Enum
from typing import Any, Optional

from shared.errors.types import ErrorCode


class ErrorCategory(str, Enum):
    """Standard error categories matching :class:`~shared.errors.types.ErrorCode`."""

    INVALID_INPUT = ErrorCode.INVALID_INPUT.value
    UNAUTHORIZED = ErrorCode.UNAUTHORIZED.value
    NOT_FOUND = ErrorCode.NOT_FOUND.value
    INTERNAL = ErrorCode.INTERNAL.value
    UNAVAILABLE = ErrorCode.UNAVAILABLE.value


class YosaiException(Exception):
    """Base application exception conforming to the error contract."""

    def __init__(
        self,
        category: ErrorCategory,
        message: str,
        details: Optional[Any] = None,
    ) -> None:
        self.category = category
        self.message = message
        self.details = details
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.category.value,
            "message": self.message,
            "details": self.details,
        }


__all__ = ["ErrorCategory", "YosaiException"]
