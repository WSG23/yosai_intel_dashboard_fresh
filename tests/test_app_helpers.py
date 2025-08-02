import types

import pytest

try:  # pragma: no cover
    import app  # type: ignore
except Exception:  # pragma: no cover
    app = None
    pytestmark = pytest.mark.skip("app module not available")


class DummyAppConfig:
    host = "127.0.0.1"
    port = 1234
    debug = False
    environment = "development"


class DummyConfig:
    def get_app_config(self):
        return DummyAppConfig()


def test_load_config(monkeypatch):
    calls = {}
    monkeypatch.setattr(
        app, "verify_dependencies", lambda: calls.setdefault("deps", True)
    )
    monkeypatch.setattr(app, "load_dotenv", lambda: calls.setdefault("dotenv", True))
    monkeypatch.setattr(
        "config.dev_mode.setup_dev_mode", lambda: calls.setdefault("setup", True)
    )

    class Loader:
        def load(self):
            calls["load"] = True
            return {}

    monkeypatch.setattr(app, "ConfigLoader", lambda: Loader())
    monkeypatch.setattr("config.get_config", lambda: DummyConfig())

    cfg = app._load_config()
    assert isinstance(cfg, DummyAppConfig)
    assert calls == {"dotenv": True, "setup": True, "load": True, "deps": True}


def test_validate_secrets_production_failure(monkeypatch):
    class DummyManager:
        def get(self, key, default=None):
            return "bad"

    class DummyValidator:
        def __init__(self, manager=None):
            pass

        def validate_secret(self, secret, environment="production"):
            return {"errors": ["bad"]}

    monkeypatch.setattr("core.secret_manager.SecretsManager", lambda: DummyManager())
    monkeypatch.setattr(
        "security.secrets_validator.SecretsValidator", lambda m=None: DummyValidator()
    )

    cfg = types.SimpleNamespace(environment="production")
    with pytest.raises(app.ConfigurationError):
        app._validate_secrets(cfg)


def test_validate_secrets_non_production(monkeypatch):
    class DummyManager:
        def get(self, key, default=None):
            return "good"

    class DummyValidator:
        def __init__(self, manager=None):
            pass

        def validate_secret(self, secret, environment="production"):
            return {"errors": []}

    monkeypatch.setattr("core.secret_manager.SecretsManager", lambda: DummyManager())
    monkeypatch.setattr(
        "security.secrets_validator.SecretsValidator", lambda m=None: DummyValidator()
    )

    cfg = types.SimpleNamespace(environment="development")
    app._validate_secrets(cfg)


def test_create_app(monkeypatch):
    class DummyApp:
        pass

    captured = {}
    monkeypatch.setattr(
        "core.app_factory.create_app", lambda mode, assets_folder: DummyApp()
    )

    class DummyMCS:
        def __init__(self, app):
            captured["manager"] = app

    monkeypatch.setattr(
        "yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks.TrulyUnifiedCallbacks",
        DummyMCS,
    )
    monkeypatch.setattr(app, "debug_dash_asset_serving", lambda a: True)

    app_obj = app._create_app()
    assert isinstance(app_obj, DummyApp)


def test_run_server(monkeypatch):
    class DummyApp:
        def __init__(self):
            self.params = {}

        def run(self, host, port, debug, ssl_context=None):
            self.params = {
                "host": host,
                "port": port,
                "debug": debug,
                "ssl": ssl_context,
            }

    dummy = DummyApp()
    monkeypatch.setattr("config.get_config", lambda: DummyConfig())

    app._run_server(dummy, None)
    assert dummy.params["ssl"] is None
    assert dummy.params["host"] == "127.0.0.1"
    assert dummy.params["port"] == "1234" or dummy.params["port"] == 1234

    dummy_ssl = DummyApp()
    app._run_server(dummy_ssl, ("cert", "key"))
    assert dummy_ssl.params["ssl"] == ("cert", "key")
