import pytest
from simple_di import ServiceContainer
from yosai_intel_dashboard.src.services.greeting import GreetingService
from pages.greetings.callbacks import register_callbacks

pytestmark = pytest.mark.usefixtures("fake_dash")


def test_register_callbacks_injects_service(monkeypatch):
    import dash

    app = dash.Dash(__name__)
    container = ServiceContainer()
    svc = GreetingService()
    container.register("greeting_service", svc)

    captured = {}

    def fake_callback(*args, **kwargs):
        def decorator(func):
            captured["func"] = func
            return func
        return decorator

    monkeypatch.setattr(app, "callback", fake_callback)

    register_callbacks(app, container)

    assert "func" in captured
    cb = captured["func"]
    assert cb("Bob") == "Hello, Bob!"


def test_app_factory_builds_container(monkeypatch):
    import app as app_module

    captured = {}

    def fake_callback(*args, **kwargs):
        def decorator(func):
            captured["func"] = func
            return func
        return decorator

    monkeypatch.setattr(app_module.Dash, "callback", fake_callback, raising=False)

    dash_app = app_module.create_app()
    assert isinstance(dash_app._container.get("greeting_service"), GreetingService)
    cb = captured["func"]
    assert cb("Alice") == "Hello, Alice!"
