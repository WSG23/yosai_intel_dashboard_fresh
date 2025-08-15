from dataclasses import dataclass
from typing import Any, Optional, Tuple

from fastapi.responses import JSONResponse

from .types import CODE_TO_STATUS, ErrorCode


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
        from yosai_intel_dashboard.src.core.exceptions import (  # type: ignore
            YosaiBaseException,
        )
    except Exception:  # pragma: no cover - imported lazily
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


def fastapi_error_response(
    error: ServiceError, status_code: Optional[int] = None
) -> JSONResponse:
    """Return a FastAPI ``JSONResponse`` for *error*.

    This wraps :func:`error_response` to ensure a consistent error payload and
    HTTP status code across services.
    """
    body, status = error_response(error, status_code)
    return JSONResponse(content=body, status_code=status)


__all__ = [
    "ServiceError",
    "from_exception",
    "error_response",
    "fastapi_error_response",
]
