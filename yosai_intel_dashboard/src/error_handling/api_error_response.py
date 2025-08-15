from __future__ import annotations

from typing import Any

from flask import Response, jsonify, has_app_context

from shared.errors.types import CODE_TO_STATUS, ErrorCode

from .core import ErrorHandler
from .exceptions import ErrorCategory


def api_error_response(
    exc: Exception,
    category: ErrorCategory = ErrorCategory.INTERNAL,
    *,
    handler: ErrorHandler | None = None,
    details: Any | None = None,
) -> tuple[Response | dict[str, Any], int]:
    """Return a JSON error response for *exc* using ``ErrorHandler``.

    When called within a Flask application context the first element of the
    returned tuple is a :class:`flask.Response` generated via ``jsonify``.  If
    no Flask context is active (e.g. when used by FastAPI middleware) a plain
    ``dict`` payload is returned instead.  This allows the same helper to be
    used by both Flask and FastAPI services while preserving the response
    format.
    """

    h = handler or ErrorHandler()
    err = h.handle(exc, category, details)
    status = CODE_TO_STATUS.get(ErrorCode(err.category.value), 500)
    payload: dict[str, Any] = err.to_dict()
    if has_app_context():
        return jsonify(payload), status
    return payload, status
