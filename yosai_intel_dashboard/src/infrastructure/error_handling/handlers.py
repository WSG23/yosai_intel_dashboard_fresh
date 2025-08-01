from __future__ import annotations

from typing import Any, Optional

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from yosai_intel_dashboard.src.core.exceptions import YosaiBaseException
from shared.errors.types import ErrorCode

from ...core.error_handling import ErrorCategory, ErrorSeverity, error_handler

_CODE_TO_STATUS: dict[ErrorCode, int] = {
    ErrorCode.INVALID_INPUT: 400,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.INTERNAL: 500,
    ErrorCode.UNAVAILABLE: 503,
}


def _json_body(code: ErrorCode | str, message: str, details: Optional[Any] = None):
    if isinstance(code, ErrorCode):
        code = code.value
    body = {"code": code, "message": message}
    if details is not None:
        body["details"] = details
    return jsonify(body)


def register_error_handlers(app: Flask) -> None:
    """Register global JSON error handlers on *app*."""

    @app.errorhandler(YosaiBaseException)
    def _handle_yosai_error(error: YosaiBaseException):  # type: ignore[missing-return-type]
        error_handler.handle_error(
            error,
            category=ErrorCategory.USER_INPUT,
            severity=ErrorSeverity.MEDIUM,
            context={"code": error.error_code.value, "message": error.message},
        )
        status = _CODE_TO_STATUS.get(error.error_code, 500)
        return _json_body(error.error_code, error.message, error.details), status

    @app.errorhandler(HTTPException)
    def _handle_http_exception(error: HTTPException):  # type: ignore[missing-return-type]
        code = error.code or 500
        mapping = {
            400: ErrorCode.INVALID_INPUT,
            401: ErrorCode.UNAUTHORIZED,
            404: ErrorCode.NOT_FOUND,
            503: ErrorCode.UNAVAILABLE,
        }
        err_code = mapping.get(code, ErrorCode.INTERNAL)
        error_handler.handle_error(
            error,
            category=ErrorCategory.USER_INPUT,
            severity=ErrorSeverity.MEDIUM,
            context={"http_code": code, "path": getattr(error, "name", "")},
        )
        return _json_body(err_code, error.description), code

    @app.errorhandler(Exception)
    def _handle_generic(error: Exception):  # type: ignore[missing-return-type]
        error_handler.handle_error(error, severity=ErrorSeverity.HIGH)
        return _json_body(ErrorCode.INTERNAL, str(error)), 500
