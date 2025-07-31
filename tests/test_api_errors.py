from yosai_intel_dashboard.src.error_handling.api_errors import http_error
from shared.errors.types import ErrorCode


def test_http_error_returns_exception():
    exc = http_error(ErrorCode.INVALID_INPUT, "bad request", 400)
    assert exc.status_code == 400
    assert exc.detail == {"code": "invalid_input", "message": "bad request"}
