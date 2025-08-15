from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse

from shared.errors.helpers import ServiceError, fastapi_error_response as build_json_response
from shared.errors.types import CODE_TO_STATUS, ErrorCode

from .core import ErrorHandler
from .exceptions import ErrorCategory


def serialize_error(
    exc: Exception,
    category: ErrorCategory = ErrorCategory.INTERNAL,
    *,
    handler: ErrorHandler | None = None,
    details: Any | None = None,
) -> tuple[dict[str, Any], int]:
    """Validate *exc* and return an error payload and HTTP status."""
    h = handler or ErrorHandler()
    err = h.handle(exc, category, details)
    status = CODE_TO_STATUS.get(ErrorCode(err.category.value), 500)
    return err.to_dict(), status


def api_error_response(
    exc: Exception,
    category: ErrorCategory = ErrorCategory.INTERNAL,
    *,
    handler: ErrorHandler | None = None,
    details: Any | None = None,
) -> tuple[dict[str, Any], int]:
    """Return a serialized payload for *exc* using ``ErrorHandler``."""
    return serialize_error(exc, category, handler=handler, details=details)


def fastapi_error_response(
    exc: Exception,
    category: ErrorCategory = ErrorCategory.INTERNAL,
    *,
    handler: ErrorHandler | None = None,
    details: Any | None = None,
) -> JSONResponse:
    """Return a FastAPI ``JSONResponse`` for *exc* using ``ErrorHandler``."""
    payload, status = serialize_error(exc, category, handler=handler, details=details)
    err = ServiceError(
        ErrorCode(payload["code"]), payload["message"], payload.get("details")
    )
    return build_json_response(err, status)


__all__ = ["serialize_error", "api_error_response", "fastapi_error_response"]
