import app

class DummyApp:
    def run_server(self, **kwargs):
        pass

class DummyAppConfig:
    debug = False
    host = "127.0.0.1"
    port = 8050
    environment = "test"

class DummyConfig:
    def get_app_config(self):
        return DummyAppConfig

def test_load_dotenv_invoked(monkeypatch):
    called = {"flag": False}

    def fake_load():
        called["flag"] = True

    monkeypatch.setattr(app, "load_dotenv", fake_load)
    monkeypatch.setattr("core.app_factory.create_app", lambda: DummyApp())
    monkeypatch.setattr("config.config.get_config", lambda: DummyConfig())
    monkeypatch.setattr(app, "print_startup_info", lambda cfg: None)

    app.main()
    assert called["flag"] is True
