from dataclasses import dataclass
from typing import Any, Optional, Tuple

from shared.errors.types import ErrorCode

# Mapping of error codes to HTTP status codes
CODE_TO_STATUS: dict[ErrorCode, int] = {
    ErrorCode.INVALID_INPUT: 400,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.INTERNAL: 500,
    ErrorCode.UNAVAILABLE: 503,
}


@dataclass
class ServiceError(Exception):
    """Represents a standardized service error."""

    code: ErrorCode | str
    message: str
    details: Optional[Any] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code.value if isinstance(self.code, ErrorCode) else self.code,
            "message": self.message,
            "details": self.details,
        }


def from_exception(exc: Exception) -> "ServiceError":
    """Create a ``ServiceError`` from any exception."""
    if isinstance(exc, ServiceError):
        return exc
    try:
        from yosai_intel_dashboard.src.core.exceptions import YosaiBaseException
    except Exception:
        YosaiBaseException = Exception  # type: ignore
    if isinstance(exc, YosaiBaseException):
        return ServiceError(
            exc.error_code,
            getattr(exc, "message", str(exc)),
            getattr(exc, "details", None),
        )
    return ServiceError(ErrorCode.INTERNAL, str(exc))


def error_response(
    error: ServiceError, status_code: Optional[int] = None
) -> Tuple[dict[str, Any], int]:
    """Return a JSON serialisable body and status code for the error."""
    status = status_code
    if status is None:
        code = error.code if isinstance(error.code, ErrorCode) else ErrorCode.INTERNAL
        status = CODE_TO_STATUS.get(code, 500)
    return error.to_dict(), status
