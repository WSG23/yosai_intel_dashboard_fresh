"""Sample Dash application wiring pages and services."""

from dash import Dash, html

from yosai_intel_dashboard.src.adapters.ui.pages import greetings
from yosai_intel_dashboard.src.callbacks import register_callbacks

from yosai_intel_dashboard.src.simple_di import ServiceContainer

try:  # pragma: no cover - allow running without full services package
    from yosai_intel_dashboard.src.services.greeting import GreetingService
except Exception:  # pragma: no cover - lightweight fallback

    class GreetingService:  # type: ignore[too-few-public-methods]
        def greet(self, name: str) -> str:
            return f"Hello, {name}!"


def create_app() -> Dash:
    """Build the DI container, create the Dash app and register callbacks."""
    container = ServiceContainer()
    container.register("greeting_service", GreetingService())

    app = Dash(__name__)
    app.layout = html.Div([greetings.layout()])

    # Register callbacks for all pages
    register_callbacks(app, container)

    # Expose container for testing/usage
    app._container = container
    return app


if __name__ == "__main__":
    create_app().run(debug=True)
