import pytest
from flask import Flask

try:  # pragma: no cover - optional dependency for FastAPI tests
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    _FASTAPI_AVAILABLE = True
except Exception:  # noqa: BLE001
    _FASTAPI_AVAILABLE = False

from yosai_intel_dashboard.src.error_handling import (
    ErrorCategory,
    ErrorHandlingMiddleware,
    api_error_response,
    register_error_handlers,
)


def test_api_error_response_generates_json_and_status():
    app = Flask(__name__)
    with app.app_context():
        resp, status = api_error_response(
            ValueError("bad"), ErrorCategory.INVALID_INPUT
        )
        assert status == 400
        assert resp.get_json() == {
            "code": "invalid_input",
            "message": "bad",
            "details": None,
        }


def test_flask_error_handler_returns_standard_schema():
    app = Flask(__name__)
    register_error_handlers(app)

    @app.get("/boom")
    def boom():  # pragma: no cover - execution happens via test client
        raise ValueError("boom")

    with app.test_client() as client:
        resp = client.get("/boom")
        assert resp.status_code == 500
        assert resp.get_json() == {
            "code": "internal",
            "message": "boom",
            "details": None,
        }


def test_fastapi_middleware_returns_standard_schema():
    if not _FASTAPI_AVAILABLE:
        pytest.skip("fastapi not available")

    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)

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
