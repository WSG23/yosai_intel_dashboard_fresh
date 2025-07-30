"""Sample Dash application wiring pages and services."""

from dash import Dash, html

from simple_di import ServiceContainer
from services.greeting import GreetingService


def create_app() -> Dash:
    """Build the DI container, create the Dash app and register callbacks."""
    container = ServiceContainer()
    container.register("greeting_service", GreetingService())

    from pages import greetings

    app = Dash(__name__)
    app.layout = html.Div([greetings.layout()])

    # Always register greeting callbacks
    greetings.register_callbacks(app, container)

    # Optionally register other feature callbacks
    for name in ("upload", "device_learning", "data_enhancer"):
        try:
            module = __import__(f"pages.{name}", fromlist=["register_callbacks"])
            if hasattr(module, "register_callbacks"):
                module.register_callbacks(app, container)
        except Exception:
            # Feature optional in minimal environment
            continue

    # Expose container for testing/usage
    app._container = container
    return app


if __name__ == "__main__":
    create_app().run(debug=True)
