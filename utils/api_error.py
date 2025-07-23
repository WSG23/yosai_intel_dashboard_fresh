from flask import jsonify
from typing import Any, Optional

from core.exceptions import YosaiBaseException
from shared.errors.types import ErrorCode


def error_response(code: ErrorCode | str, message: str, details: Optional[Any] = None):
    if isinstance(code, ErrorCode):
        code = code.value
    body = {"code": code, "message": message}
    if details is not None:
        body["details"] = details
    return jsonify(body)


def error_from_exception(exc: YosaiBaseException):
    return error_response(exc.error_code, exc.message, exc.details)
