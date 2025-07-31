"""Sample Dash application wiring pages and services."""

from dash import Dash, html

from pages import greetings, register_callbacks
from services.greeting import GreetingService
from simple_di import ServiceContainer


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
