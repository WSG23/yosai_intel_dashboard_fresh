import pytest

from shared.errors.types import ErrorCode
from yosai_framework.errors import ServiceError, error_response


def test_error_response_defaults():
    err = ServiceError(ErrorCode.NOT_FOUND, "missing")
    body, status = error_response(err)
    assert status == 404
    assert body == {"code": "not_found", "message": "missing", "details": None}


def test_error_response_custom_status():
    err = ServiceError(ErrorCode.UNAUTHORIZED, "nope")
    body, status = error_response(err, 418)
    assert status == 418
    assert body == {"code": "unauthorized", "message": "nope", "details": None}
