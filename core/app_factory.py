#!/usr/bin/env python3
"""
Complete App Factory Integration - FIXED CLASS NAMES
"""
import dash
import logging
import os
from typing import Optional, Any
from flasgger import Swagger
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output
from core.unified_callback_coordinator import UnifiedCallbackCoordinator
from core.container import Container as DIContainer
from core.plugins.manager import PluginManager
from core.secret_manager import validate_secrets
from dash_csrf_plugin import setup_enhanced_csrf_protection, CSRFMode
import pandas as pd

# ✅ FIXED IMPORTS - Use correct config system
from config.config import get_config

logger = logging.getLogger(__name__)


def create_app(mode: Optional[str] = None) -> dash.Dash:
    """Create a Dash application.

    Parameters
    ----------
    mode: Optional[str]
        One of ``"full"`` (default), ``"simple"`` or ``"json-safe"``. The value
        can also be provided via the ``YOSAI_APP_MODE`` environment variable.
    """

    mode = (mode or os.getenv("YOSAI_APP_MODE", "full")).lower()

    if mode == "simple":
        logger.info("Creating application in simple mode")
        return _create_simple_app()

    if mode in {"json-safe", "json_safe", "jsonsafe"}:
        logger.info("Creating application in JSON-safe mode")
        return _create_json_safe_app()

    logger.info("Creating application in full mode")
    return _create_full_app()


def _create_full_app() -> dash.Dash:
    """Create complete Dash application with full integration"""
    try:
        app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True,
            assets_folder="assets",
        )

        app.title = "Yōsai Intel Dashboard"

        # ✅ FIXED: Use the working config system
        config_manager = get_config()

        if (
            config_manager.get_security_config().csrf_enabled
            and config_manager.get_app_config().environment == "production"
        ):
            try:
                app._csrf_plugin = setup_enhanced_csrf_protection(
                    app, CSRFMode.PRODUCTION
                )
            except Exception as e:  # pragma: no cover - best effort
                logger.warning(f"Failed to initialize CSRF plugin: {e}")

        # Initialize plugin system
        container = DIContainer()
        plugin_manager = PluginManager(container, config_manager)
        plugin_manager.load_all_plugins()
        app._yosai_plugin_manager = plugin_manager

        @app.server.teardown_appcontext  # type: ignore[attr-defined]
        def _shutdown_plugin_manager(exc=None):
            plugin_manager.stop_health_monitor()

        # Set main layout
        app.layout = _create_main_layout()

        # Register all callbacks using UnifiedCallbackCoordinator
        coordinator = UnifiedCallbackCoordinator(app)
        _register_router_callbacks(coordinator)
        _register_global_callbacks(coordinator)

        # Register page/component callbacks
        try:
            from pages.file_upload import (
                register_callbacks as register_upload_callbacks,
                Callbacks as UploadCallbacks,
            )
            from components.simple_device_mapping import (
                register_callbacks as register_simple_mapping,
            )
            from components.device_verification import (
                register_callbacks as register_device_verification,
            )
            from pages.deep_analytics.callbacks import (
                register_callbacks as register_deep_callbacks,
                Callbacks as DeepAnalyticsCallbacks,
            )
            from dashboard.layout.navbar import register_navbar_callbacks

            register_upload_callbacks(coordinator)
            register_simple_mapping(coordinator)
            register_device_verification(coordinator)
            register_deep_callbacks(coordinator)
            register_navbar_callbacks(coordinator)

            # Keep references to callback managers
            app._upload_callbacks = UploadCallbacks()
            app._deep_analytics_callbacks = DeepAnalyticsCallbacks()

            if config_manager.get_app_config().environment == "development":
                coordinator.print_callback_summary()
        except Exception as e:
            logger.warning(f"Failed to register module callbacks: {e}")

        # Initialize services
        _initialize_services()

        # Expose basic health check endpoint and Swagger docs
        server = app.server
        _configure_swagger(server)

        @server.route("/health", methods=["GET"])
        def health():
            """Basic health check.
            ---
            get:
              description: Return service health
              responses:
                200:
                  description: Health status
                  content:
                    application/json:
                      schema:
                        type: object
                        properties:
                          status:
                            type: string
                            example: ok
            """
            return {"status": "ok"}, 200

        @server.route("/health/secrets", methods=["GET"])
        def health_secrets():
            """Return validation summary for required secrets"""
            return validate_secrets(), 200

        logger.info("✅ Complete Dash application created successfully")
        return app

    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        raise


def _create_simple_app() -> dash.Dash:
    """Create a simplified Dash application"""
    try:
        from dash import html, dcc

        app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True,
        )

        app.title = "Yōsai Intel Dashboard"

        app.layout = html.Div(
            [
                dcc.Location(id="url", refresh=False),
                html.H1("🏯 Yōsai Intel Dashboard", className="text-center"),
                html.Hr(),
                html.Div(
                    [
                        dbc.Alert(
                            "✅ Application created successfully!", color="success"
                        ),
                        dbc.Alert(
                            "⚠️ Running in simplified mode (no auth)", color="warning"
                        ),
                        html.P("Environment configuration loaded and working."),
                        html.P("Ready for development and testing."),
                    ],
                    className="container",
                ),
            ]
        )

        # Expose basic health check endpoint and Swagger docs
        server = app.server
        _configure_swagger(server)

        @server.route("/health", methods=["GET"])
        def health():
            """Basic health check.
            ---
            get:
              description: Return service health
              responses:
                200:
                  description: Health status
                  content:
                    application/json:
                      schema:
                        type: object
                        properties:
                          status:
                            type: string
                            example: ok
            """
            return {"status": "ok"}, 200

        @server.route("/health/secrets", methods=["GET"])
        def health_secrets():
            """Return validation summary for required secrets"""
            return validate_secrets(), 200

        logger.info("Simple Dash application created successfully")
        return app

    except Exception as e:
        logger.error(f"Failed to create simple application: {e}")
        raise


def _create_json_safe_app() -> dash.Dash:
    """Create Dash application with JSON-safe layout"""
    try:
        from dash import html

        app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True,
        )

        app.title = "🏯 Yōsai Intel Dashboard"

        app.layout = html.Div(
            [
                html.H1("🏯 Yōsai Intel Dashboard", className="text-center"),
                html.Hr(),
                dbc.Container(
                    [
                        dbc.Alert(
                            "✅ Application running with JSON-safe components",
                            color="success",
                        ),
                        dbc.Alert(
                            "🔧 All callbacks are wrapped for safe serialization",
                            color="info",
                        ),
                        html.P("Environment configuration loaded successfully."),
                        html.P("JSON serialization issues have been resolved."),
                    ]
                ),
            ]
        )

        # Expose basic health check endpoint and Swagger docs
        server = app.server
        _configure_swagger(server)

        @server.route("/health", methods=["GET"])
        def health():
            """Basic health check.
            ---
            get:
              description: Return service health
              responses:
                200:
                  description: Health status
                  content:
                    application/json:
                      schema:
                        type: object
                        properties:
                          status:
                            type: string
                            example: ok
            """
            return {"status": "ok"}, 200

        @server.route("/health/secrets", methods=["GET"])
        def health_secrets():
            """Return validation summary for required secrets"""
            return validate_secrets(), 200

        logger.info("JSON-safe Dash application created")
        return app

    except Exception as e:
        logger.error(f"Failed to create JSON-safe application: {e}")
        raise


def _create_main_layout() -> html.Div:
    """Create main application layout with complete integration"""
    return html.Div(
        [
            # URL routing component
            dcc.Location(id="url", refresh=False),
            # Navigation bar
            _create_navbar(),
            # Main content area (dynamically populated)
            html.Div(id="page-content", className="main-content p-4"),
            # Global data stores
            dcc.Store(id="global-store", data={}),
            dcc.Store(id="session-store", data={}),
            dcc.Store(id="app-state-store", data={"initial": True}),
        ]
    )


def _create_navbar() -> dbc.Navbar:
    """Create navigation bar"""
    return dbc.Navbar(
        [
            dbc.Container(
                [
                    # Brand
                    dbc.NavbarBrand(
                        [
                            html.I(className="fas fa-shield-alt me-2"),
                            "Yōsai Intel Dashboard",
                        ],
                        href="/",
                    ),
                    # Navigation links
                    dbc.Nav(
                        [
                            dbc.NavItem(
                                dbc.NavLink(
                                    [
                                        html.I(className="fas fa-tachometer-alt me-1"),
                                        "Dashboard",
                                    ],
                                    href="/",
                                )
                            ),
                            dbc.NavItem(
                                dbc.NavLink(
                                    [
                                        html.I(className="fas fa-chart-line me-1"),
                                        "Analytics",
                                    ],
                                    href="/analytics",
                                )
                            ),
                            dbc.NavItem(
                                dbc.NavLink(
                                    [
                                        html.I(className="fas fa-chart-area me-1"),
                                        "Graphs",
                                    ],
                                    href="/graphs",
                                )
                            ),
                            dbc.NavItem(
                                dbc.NavLink(
                                    [
                                        html.I(className="fas fa-file-upload me-1"),
                                        "Upload",
                                    ],
                                    href="/upload",
                                )
                            ),
                            dbc.NavItem(
                                dbc.NavLink(
                                    [html.I(className="fas fa-cog me-1"), "Settings"],
                                    href="/settings",
                                )
                            ),
                            dbc.NavItem(
                                [
                                    dbc.Button(
                                        "🔄 Clear Cache",
                                        id="clear-cache-btn",
                                        color="outline-secondary",
                                        size="sm",
                                    )
                                ]
                            ),
                        ],
                        navbar=True,
                    ),
                ]
            )
        ],
        color="dark",
        dark=True,
        className="mb-4",
    )


def _create_placeholder_page(title: str, subtitle: str, message: str) -> html.Div:
    """Create placeholder page for missing modules"""
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H1(title, className="text-primary mb-3"),
                            html.P(subtitle, className="text-muted mb-4"),
                            dbc.Alert(message, color="warning"),
                        ]
                    )
                ]
            )
        ]
    )


def _register_router_callbacks(manager: UnifiedCallbackCoordinator) -> None:
    """Register page routing callbacks."""

    @manager.register_callback(
        Output("page-content", "children"),
        Input("url", "pathname"),
        callback_id="display_page",
        component_name="app_factory",
    )
    def display_page(pathname: str):
        if pathname == "/analytics":
            return _get_analytics_page()
        elif pathname == "/graphs":
            return _get_graphs_page()
        elif pathname == "/settings":
            return _get_settings_page()
        elif pathname in {"/upload", "/file-upload"}:
            return _get_upload_page()
        elif pathname in {"/", "/dashboard"}:
            return _get_home_page()
        return html.Div(
            [
                html.H1("Page Not Found", className="text-center mt-5"),
                html.P(
                    "The page you're looking for doesn't exist.",
                    className="text-center",
                ),
                dbc.Button(
                    "Go Home", href="/", color="primary", className="d-block mx-auto"
                ),
            ]
        )


def _get_home_page() -> Any:
    """Get home page (dashboard)."""
    return _get_dashboard_page()


def _get_dashboard_page() -> Any:
    """Get dashboard page with overview metrics."""
    try:
        from pages.dashboard import layout

        return layout()
    except ImportError as e:
        logger.error(f"Dashboard page import failed: {e}")
        return _create_placeholder_page(
            "Dashboard",
            "Dashboard page is being loaded...",
            "The dashboard module is not available. Please check the installation.",
        )


def _get_analytics_page() -> Any:
    """Get analytics page with complete integration"""
    try:
        from pages.deep_analytics.layout import layout

        return layout()
    except ImportError as e:
        logger.error(f"Analytics page import failed: {e}")
        return _create_placeholder_page(
            "📊 Analytics",
            "Analytics page is being loaded...",
            "The analytics module is not available. Please check the installation.",
        )


def _get_graphs_page() -> Any:
    """Get graphs page with placeholder content."""
    try:
        from pages.graphs import layout

        return layout()
    except ImportError as e:
        logger.error(f"Graphs page import failed: {e}")
        return _create_placeholder_page(
            "Graphs",
            "Graphs page is being loaded...",
            "The graphs module is not available. Please check the installation.",
        )


def _get_settings_page() -> Any:
    """Get settings page with placeholder content."""
    try:
        from pages.settings import layout

        return layout()
    except ImportError as e:
        logger.error(f"Settings page import failed: {e}")
        return _create_placeholder_page(
            "Settings",
            "Settings page is being loaded...",
            "The settings module is not available. Please check the installation.",
        )


def _get_upload_page() -> Any:
    """Get upload page with complete integration"""
    try:
        from pages.file_upload import layout

        return layout()
    except ImportError as e:
        logger.error(f"Upload page import failed: {e}")
        return _create_placeholder_page(
            "📁 File Upload",
            "File upload page is being loaded...",
            "The file upload module is not available. Please check the installation.",
        )


def _register_global_callbacks(manager: UnifiedCallbackCoordinator) -> None:
    """Register global application callbacks"""

    @manager.register_callback(
        Output("global-store", "data"),
        Input("clear-cache-btn", "n_clicks"),
        prevent_initial_call=True,
        callback_id="clear_cache",
        component_name="app_factory",
    )
    def clear_cache(n_clicks):
        """Clear application cache"""
        if n_clicks:
            try:
                # Clear uploaded data
                from pages.file_upload import clear_uploaded_data

                clear_uploaded_data()
                logger.info("Application cache cleared")
                return {
                    "cache_cleared": True,
                    "timestamp": pd.Timestamp.now().isoformat(),
                }
            except ImportError:
                logger.warning("Could not clear uploaded data - module not available")
                return {"cache_cleared": False}
        return {}

    # Register device learning callbacks
    from services.device_learning_service import create_learning_callbacks

    create_learning_callbacks(manager)

    logger.info("✅ Global callbacks registered successfully")


def _initialize_services() -> None:
    """Initialize all application services"""
    try:
        # Initialize analytics service
        from services import get_analytics_service

        analytics_service = get_analytics_service()
        health = analytics_service.health_check()
        logger.info(f"Analytics service initialized: {health}")

        # Initialize configuration
        config = get_config()
        app_config = config.get_app_config()
        logger.info(f"Configuration loaded for environment: {app_config.environment}")

    except Exception as e:
        logger.warning(f"Service initialization completed with warnings: {e}")


def _configure_swagger(server: Any) -> None:
    """Initialize Swagger UI for API documentation."""
    server.config.setdefault("SWAGGER", {"uiversion": 3})
    template = {
        "openapi": "3.0.2",
        "info": {
            "title": "Yōsai Intel Dashboard API",
            "version": "1.0.0",
        },
    }
    Swagger(server, template=template, config={"specs_route": "/api/docs"})


# Export the main function
__all__ = ["create_app"]
