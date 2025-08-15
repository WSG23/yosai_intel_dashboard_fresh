"""Sample Dash application wiring pages and services."""

from dash import Dash, html
from flask import Response
from flask_wtf.csrf import CSRFProtect

from yosai_intel_dashboard.src.adapters.ui.pages import greetings
from yosai_intel_dashboard.src.callbacks import register_callbacks

from yosai_intel_dashboard.src.simple_di import ServiceContainer
from yosai_intel_dashboard.src.core.secret_manager import SecretsManager, validate_secrets

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

    manager = SecretsManager()
    summary = validate_secrets(manager)
    if not summary["valid"]:
        missing = ", ".join(summary["missing"])
        raise RuntimeError(f"Missing required secrets: {missing}")

    app = Dash(__name__)
    server = app.server
    secret_key = manager.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY is required")
    server.config["SECRET_KEY"] = secret_key
    CSRFProtect(server)

    @server.after_request
    def _set_csp(response: Response) -> Response:
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'")
        return response

    app.layout = html.Div([greetings.layout()])

    # Register callbacks for all pages
    register_callbacks(app, container)

    # Expose container for testing/usage
    app._container = container
    return app


app = create_app()


@app.server.get("/health")
def _health() -> Response:  # pragma: no cover - simple health endpoint
    return Response("ok", 200)


if __name__ == "__main__":
    app.run(debug=False)
