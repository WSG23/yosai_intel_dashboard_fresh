import json
import pytest
try:  # pragma: no cover - optional dependency for FastAPI tests
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    _FASTAPI_AVAILABLE = True
except Exception:  # noqa: BLE001
    _FASTAPI_AVAILABLE = False

from yosai_intel_dashboard.src.error_handling import (
    ErrorCategory,
    ErrorHandler,
    ErrorHandlingMiddleware,
    fastapi_error_response,
    serialize_error,
)
from yosai_intel_dashboard.src.error_handling import core as error_core

# Disable error budget metrics during tests to avoid requiring Prometheus internals
error_core.record_error = lambda service: None

# Disable metric recording during tests to avoid Prometheus dependency
from yosai_intel_dashboard.src.error_handling import core as err_core

err_core.record_error = lambda service: None


@pytest.mark.skip("requires monitoring metrics")
def test_flask_error_handler_returns_standard_schema():
    pass


def test_fastapi_middleware_returns_standard_schema():
    if not _FASTAPI_AVAILABLE:
        pytest.skip("fastapi not available")

    app = FastAPI()
    ErrorHandlingMiddleware.setup(app)

    @app.get("/boom")
    async def boom():  # pragma: no cover - executed by TestClient
        raise ValueError("boom")

    with TestClient(app) as client:
        resp = client.get("/boom")
        assert resp.status_code == 500
        assert resp.json() == {
            "code": "internal",
            "message": "boom",
            "details": None,
        }

def test_serialize_error_returns_payload_and_status():
    payload, status = serialize_error(ValueError("oops"), ErrorCategory.INVALID_INPUT)
    assert status == 400
    assert payload == {"code": "invalid_input", "message": "oops", "details": None}


def test_fastapi_error_response_returns_json_response():
    resp = fastapi_error_response(ValueError("bad"))
    assert resp.status_code == 500
    assert json.loads(resp.body) == {
        "code": "internal",
        "message": "bad",
        "details": None,
    }
