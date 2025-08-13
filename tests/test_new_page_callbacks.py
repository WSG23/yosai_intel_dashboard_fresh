import pytest
from yosai_intel_dashboard.src.simple_di import ServiceContainer


class GreetingService:
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"


def test_register_callbacks_injects_service():
    import dash
    from yosai_intel_dashboard.src.callbacks import controller as controller_module

    register_greetings_callbacks = controller_module.register_greetings_callbacks

    app = dash.Dash(__name__)
    container = ServiceContainer()
    svc = GreetingService()
    container.register("greeting_service", svc)

    captured = {}

    class DummyCallbacks:
        def __init__(self, app):
            self.app = app

        def callback(self, *args, **kwargs):
            def decorator(func):
                captured["func"] = func
                return func

            return decorator

    callbacks = DummyCallbacks(app)

    register_greetings_callbacks(callbacks, container)

    assert "func" in captured
    cb = captured["func"]
    assert cb("Bob") == "Hello, Bob!"


def test_app_factory_builds_container(monkeypatch):
    from yosai_intel_dashboard.src import app as app_module
    from yosai_intel_dashboard.src.callbacks import controller as controller_module

    captured = {}

    class DummyCallbacks:
        def __init__(self, app):
            self.app = app

        def callback(self, *args, **kwargs):
            def decorator(func):
                captured["func"] = func
                return func

            return decorator

    monkeypatch.setattr(controller_module, "TrulyUnifiedCallbacks", DummyCallbacks)
    monkeypatch.setattr(
        controller_module, "register_upload_callbacks", lambda *a, **k: None
    )
    monkeypatch.setattr(
        controller_module,
        "register_device_learning_callbacks",
        lambda *a, **k: None,
    )

    dash_app = app_module.create_app()
    svc = dash_app._container.get("greeting_service")
    assert svc.greet("Alice") == "Hello, Alice!"
    cb = captured["func"]
    assert cb("Alice") == "Hello, Alice!"
