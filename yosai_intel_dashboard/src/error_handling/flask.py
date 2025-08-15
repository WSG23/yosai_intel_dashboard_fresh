"""Flask integration for the shared error handling contract."""

from flask import Flask, jsonify

from shared.errors.types import CODE_TO_STATUS, ErrorCode

from .core import ErrorHandler
from .exceptions import ErrorCategory, YosaiException


def register_error_handlers(app: Flask, handler: ErrorHandler | None = None) -> None:
    """Register a generic exception handler returning ``ErrorResponse`` payloads."""

    err_handler = handler or ErrorHandler()

    @app.errorhandler(Exception)
    def _handle(exc: Exception):  # type: ignore[override]
        if isinstance(exc, YosaiException):
            err = exc
        else:
            err = err_handler.handle(exc, ErrorCategory.INTERNAL)
        status = CODE_TO_STATUS.get(ErrorCode(err.category.value), 500)
        return jsonify(err.to_dict()), status


__all__ = ["register_error_handlers"]

