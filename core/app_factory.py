"""Complete app factory with full DI integration."""
from __future__ import annotations

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc

from core.service_container import ServiceContainer
from core.unicode_processor import safe_format_text
from config.complete_service_registration import register_all_application_services


class AppFactory:
    """Factory for creating fully configured Dash app with DI."""

    def __init__(self):
        self.container = ServiceContainer()
        self._app = None

    def create_app(self, config_override: dict = None) -> dash.Dash:
        """Create and configure complete Dash application."""
        if self._app is not None:
            return self._app

        # 1. Create Dash app
        self._app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True,
        )
        # Expose factory on the app instance for tests
        setattr(self._app, "_yosai_app_factory", self)

        # 2. Register all services with DI container
        register_all_application_services(self.container)

        # 3. Configure app with DI
        self._configure_app_with_di(config_override or {})

        # 4. Setup layout with DI
        self._setup_layout_with_di()

        # 5. Register all callbacks with DI
        self._register_callbacks_with_di()

        return self._app

    def _configure_app_with_di(self, config_override: dict) -> None:
        """Configure app using DI container services."""
        config_manager = self.container.get("config_manager")

        # Apply configuration
        app_config = config_manager.get_app_config()
        for key, value in app_config.__dict__.items():
            if key.upper() not in config_override:
                self._app.server.config[key.upper()] = value

        # Apply overrides
        for key, value in config_override.items():
            self._app.server.config[key.upper()] = value

        # Initialize other services
        logging_service = self.container.get("logging_service")
        logging_service.configure_app_logging(self._app)

    def _setup_layout_with_di(self) -> None:
        """Setup app layout using DI container."""
        self._app.layout = html.Div([
            dcc.Location(id="url", refresh=False),
            html.Div(id="page-content"),
            dcc.Store(id="session-store"),
            dcc.Store(id="theme-store", data="light"),
        ])

    def _register_callbacks_with_di(self) -> None:
        """Register all callbacks with DI container access."""
        from pages.upload_page import register_upload_callbacks
        from pages.analytics_page import register_analytics_callbacks
        from components.ui.navbar import register_navbar_callbacks

        # Pass container to callback registration functions
        register_upload_callbacks(self._app, self.container)
        register_analytics_callbacks(self._app, self.container)
        register_navbar_callbacks(self._app, self.container)

    def get_container(self) -> ServiceContainer:
        """Get the DI container for testing."""
        return self.container


def create_app(config_override: dict = None) -> dash.Dash:
    """Convenience function to create app."""
    factory = AppFactory()
    return factory.create_app(config_override)


__all__ = ["AppFactory", "create_app"]
