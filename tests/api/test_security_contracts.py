from starlette.testclient import TestClient
from api.main import app


def test_health_ok():
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200


def test_security_headers_present():
    c = TestClient(app)
    r = c.get("/health")
    h = r.headers
    assert h.get("X-Content-Type-Options") == "nosniff"
    assert h.get("X-Frame-Options") == "DENY"
    assert h.get("Referrer-Policy") == "no-referrer"


def test_payload_limit_enforced():
    c = TestClient(app)
    big = "x" * (50 * 1024 * 1024 + 1)
    r = c.post("/api/v1/echo", json={"message": big})
    assert r.status_code in (400, 413)
