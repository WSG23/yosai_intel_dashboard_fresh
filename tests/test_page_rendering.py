"""Smoke tests ensuring pages render after callback registration."""

import dash
from dash import html

from yosai_intel_dashboard.src.callbacks import controller
from yosai_intel_dashboard.src.simple_di import ServiceContainer
from yosai_intel_dashboard.src.adapters.ui.pages import greetings


class GreetingService:
    def greet(self, name: str) -> str:  # pragma: no cover - simple DI stub
        return f"Hello, {name}!"


def test_greetings_page_renders(monkeypatch):
    """Verify that the greetings page renders without errors."""

    app = dash.Dash(__name__)
    container = ServiceContainer()
    container.register("greeting_service", GreetingService())

    class DummyCallbacks:
        def __init__(self, app):
            self.app = app

        def callback(self, *args, **kwargs):  # pragma: no cover - simple pass-through
            def decorator(func):
                return func

            return decorator

    # Use dummy callback registry to avoid heavy infrastructure imports
    monkeypatch.setattr(controller, "TrulyUnifiedCallbacks", DummyCallbacks)
    # Simplify by disabling other callback registrations
    monkeypatch.setattr(controller, "register_upload_callbacks", lambda *a, **k: None)
    monkeypatch.setattr(
        controller, "register_device_learning_callbacks", lambda *a, **k: None
    )

    app.layout = html.Div([greetings.layout()])

    controller.register_callbacks(app, container)
    # Ensure layout contains expected component
    children = app.layout.children[0].children
    assert any(getattr(child, "id", None) == "greet-output" for child in children)

