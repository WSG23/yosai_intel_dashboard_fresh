from __future__ import annotations

from typing import Any, Tuple

from flask import Response, jsonify

from shared.errors.types import ErrorCode

CODE_TO_STATUS: dict[ErrorCode, int] = {
    ErrorCode.INVALID_INPUT: 400,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.INTERNAL: 500,
    ErrorCode.UNAVAILABLE: 503,
}

from .core import ErrorHandler
from .exceptions import ErrorCategory


def api_error_response(
    exc: Exception,
    category: ErrorCategory = ErrorCategory.INTERNAL,
    *,
    handler: ErrorHandler | None = None,
    details: Any | None = None,
) -> tuple[Response, int]:
    """Return a JSON error response for *exc* using ``ErrorHandler``."""
    h = handler or ErrorHandler()
    err = h.handle(exc, category, details)
    status = CODE_TO_STATUS.get(ErrorCode(err.category.value), 500)
    return jsonify(err.to_dict()), status
