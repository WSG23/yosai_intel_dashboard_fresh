import pytest

pytestmark = pytest.mark.usefixtures("fake_dash")

try:  # pragma: no cover
    from yosai_intel_dashboard.src.pages.greetings.callbacks import register_callbacks
    from yosai_intel_dashboard.src.services.greeting import GreetingService
    from yosai_intel_dashboard.src.simple_di import ServiceContainer
except Exception:  # pragma: no cover
    register_callbacks = None  # type: ignore
    GreetingService = ServiceContainer = None  # type: ignore
    pytestmark = pytest.mark.skip("pages module not available")


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
    try:  # pragma: no cover
        import app as app_module  # type: ignore
    except Exception:  # pragma: no cover
        from yosai_intel_dashboard.src import app as app_module

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
