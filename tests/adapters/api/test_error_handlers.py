from fastapi import FastAPI
from fastapi.testclient import TestClient

from yosai_intel_dashboard.src.error_handling.middleware import ErrorHandlingMiddleware
from yosai_intel_dashboard.src.core.exceptions import ServiceUnavailableError, ValidationError


def _create_app() -> FastAPI:
    app = FastAPI()
    ErrorHandlingMiddleware.setup(app)

    @app.get("/fail")
    def fail_route():
        raise ValidationError("bad")

    @app.get("/unavail")
    def unavail_route():
        raise ServiceUnavailableError("maintenance")

    @app.get("/internal")
    def internal_route():
        raise RuntimeError("boom")

    return app


def test_yosai_base_exception_handled():
    client = TestClient(_create_app())
    resp = client.get("/fail")
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "invalid_input"
    assert body["message"] == "bad"
    assert body["details"] == {}


def test_service_unavailable_error():
    client = TestClient(_create_app())
    resp = client.get("/unavail")
    assert resp.status_code == 503
    assert resp.json() == {
        "code": "unavailable",
        "message": "maintenance",
        "details": {},
    }


def test_generic_exception_handled():
    client = TestClient(_create_app())
    resp = client.get("/internal")
    assert resp.status_code == 500
    body = resp.json()
    assert body["code"] == "internal"
    assert body["message"] == "boom"
    assert body["details"] is None
