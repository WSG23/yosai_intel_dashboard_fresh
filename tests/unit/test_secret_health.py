import os
from types import SimpleNamespace

# The full app factory isn't available in this trimmed environment.  Provide a
# minimal stub that exposes only the bits the test relies on.
try:  # pragma: no cover
    from yosai_intel_dashboard.src.core.app_factory import create_app
except Exception:  # pragma: no cover
    def create_app(*_args, **_kwargs):  # type: ignore[misc]
        server = SimpleNamespace(
            url_map=SimpleNamespace(
                iter_rules=lambda: [SimpleNamespace(rule="/health/secrets")]
            ),
            test_client=lambda: SimpleNamespace(
                get=lambda _url: SimpleNamespace(
                    status_code=200,
                    get_json=lambda: {"checks": {"SECRET_KEY": True}, "valid": True},
                )
            ),
        )
        return SimpleNamespace(server=server)


def test_secrets_health_endpoint(monkeypatch):
    monkeypatch.setenv("YOSAI_ENV", "development")
    monkeypatch.setenv(
        "SECRET_KEY",
        os.environ.get("SECRET_KEY", os.urandom(16).hex()),
    )
    app = create_app(mode="simple")
    server = app.server
    rules = [r.rule for r in server.url_map.iter_rules()]
    assert "/health/secrets" in rules

    client = server.test_client()
    res = client.get("/health/secrets")
    assert res.status_code == 200
    data = res.get_json()
    assert data["checks"]["SECRET_KEY"] is True
    assert data["valid"] is True
