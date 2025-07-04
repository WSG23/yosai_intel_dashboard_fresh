#!/usr/bin/env python3
"""Complete application factory integration."""
import dash
import logging
import os
from pathlib import Path
from typing import Optional, Any
from flasgger import Swagger
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output
from components.ui.navbar import create_navbar_layout
from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from core.container import Container as DIContainer
from core.plugins.auto_config import PluginAutoConfiguration
from core.secret_manager import validate_secrets
from dash_csrf_plugin import setup_enhanced_csrf_protection, CSRFMode
from flask_babel import Babel
from flask import session
from flask_compress import Compress
from flask_talisman import Talisman
from core.theme_manager import apply_theme_settings, DEFAULT_THEME, sanitize_theme
from config.config import get_config
from .cache import cache

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
BUNDLE = "/assets/dist/main.min.css"

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
        external_stylesheets = [dbc.themes.BOOTSTRAP]
        built_css = ASSETS_DIR / "dist" / "main.min.css"
        assets_ignore = r".*\.map|css/_.*"
        if built_css.exists():
            external_stylesheets.append("/assets/dist/main.min.css")
            assets_ignore += r"|css/main\.css"
        assets_ignore = rf"^\..*|.*\.txt$|{assets_ignore}"
        assets_ignore = rf"^\..*|.*\.txt$|{assets_ignore}"
        # Ignore hidden files and text assets but allow everything else
        assets_ignore = rf"^\..*|.*\.txt$|{assets_ignore}"

        app = dash.Dash(
            __name__,
            external_stylesheets=external_stylesheets,
            suppress_callback_exceptions=True,
            assets_folder=str(ASSETS_DIR),
            assets_ignore=assets_ignore,
        )

        cache.init_app(app.server)
        app.cache = cache

        app.index_string = f"""
<!DOCTYPE html>
<html>
  <head>
    {{%metas%}}
    <title>Yōsai Intel Dashboard</title>
    <link rel=\"stylesheet\" href=\"{BUNDLE}\" />
    {{%favicon%}}
    {{%css%}}
  </head>
  <body>
    {{%app_entry%}}
    <footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer>
  </body>
</html>
"""

        # Set a temporary layout so Dash can handle requests during
        # the asset serving check without raising ``NoLayoutException``.
        # The final layout is assigned later once all plugins are loaded.
        app.layout = html.Div()

        # Asset serving check has been moved out of the factory to ensure
        # request handlers can be registered before the first request is
        # processed.  The server can still be validated after creation by
        # calling :func:`utils.assets_debug.debug_dash_asset_serving`.

        apply_theme_settings(app)
        Compress(app.server)
        config_manager = get_config()
        https_only = config_manager.get_app_config().environment == "production"
        Talisman(
            app.server,
            content_security_policy=None,
            force_https=https_only,
            force_https_permanent=https_only,
        )

        @app.server.after_request  # type: ignore[misc]
        def add_cache_headers(resp):
            if resp.mimetype and resp.mimetype.startswith(
                ("text/", "application/javascript", "image/")
            ):
                resp.headers["Cache-Control"] = "public,max-age=31536000,immutable"
            return resp

        app.title = "Yōsai Intel Dashboard"

        # Initialize Flask-Babel before any layouts use gettext
        try:
            babel = Babel(app.server)

            def _select_locale() -> str:
                return session.get("locale", "en")

            if hasattr(babel, "localeselector"):
                babel.localeselector(_select_locale)  # Flask-Babel <4
            elif hasattr(babel, "locale_selector_func"):
                babel.locale_selector_func(_select_locale)  # Flask-Babel 3.x
            else:  # pragma: no cover - Flask-Babel >=4
                babel.locale_selector = _select_locale  # type: ignore[attr-defined]
            app.server.babel = babel
        except Exception as e:  # pragma: no cover - optional dependency
            logger.warning(f"Failed to initialize Babel: {e}")

        # Use the working config system

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

        # Initialize plugin system via unified registry
        container = DIContainer()
        plugin_auto = PluginAutoConfiguration(
            app,
            container=container,
            config_manager=config_manager,
        )
        plugin_auto.scan_and_configure("plugins")
        plugin_auto.generate_health_endpoints()
        registry = plugin_auto.registry
        app._yosai_plugin_manager = registry.plugin_manager

        @app.server.teardown_appcontext  # type: ignore[attr-defined]
        def _shutdown_plugin_manager(exc=None):
            registry.plugin_manager.stop_all_plugins()
            registry.plugin_manager.stop_health_monitor()

        # Set main layout with caching to avoid repeated JSON encoding
        layout_snapshot = None

        def _serve_layout():
            nonlocal layout_snapshot
            if layout_snapshot is None:
                layout_snapshot = _create_main_layout()
            return layout_snapshot

        app.layout = _serve_layout

        # Register all callbacks using TrulyUnifiedCallbacks
        coordinator = TrulyUnifiedCallbacks(app)
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
            from components.ui.navbar import register_navbar_callbacks

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

        external_stylesheets = [dbc.themes.BOOTSTRAP]
        built_css = ASSETS_DIR / "dist" / "main.min.css"
        assets_ignore = r".*\.map|css/_.*"
        if built_css.exists():
            external_stylesheets.append("/assets/dist/main.min.css")
            assets_ignore += r"|css/main\.css"

        app = dash.Dash(
            __name__,
            external_stylesheets=external_stylesheets,
            suppress_callback_exceptions=True,
            assets_ignore=assets_ignore,
        )

        cache.init_app(app.server)
        app.cache = cache

        cache.init_app(app.server)
        app.cache = cache

        app.index_string = f"""
<!DOCTYPE html>
<html>
  <head>
    {{%metas%}}
    <title>Yōsai Intel Dashboard</title>
    <link rel=\"stylesheet\" href=\"{BUNDLE}\" />
    {{%favicon%}}
    {{%css%}}
  </head>
  <body>
    {{%app_entry%}}
    <footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer>
  </body>
</html>
"""

        apply_theme_settings(app)
        Compress(app.server)
        cfg = get_config()
        https_only = cfg.get_app_config().environment == "production"
        Talisman(
            app.server,
            content_security_policy=None,
            force_https=https_only,
            force_https_permanent=https_only,
        )

        @app.server.after_request  # type: ignore[misc]
        def add_cache_headers(resp):
            if resp.mimetype and resp.mimetype.startswith(
                ("text/", "application/javascript", "image/")
            ):
                resp.headers["Cache-Control"] = "public,max-age=31536000,immutable"
            return resp

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

        external_stylesheets = [dbc.themes.BOOTSTRAP]
        built_css = ASSETS_DIR / "dist" / "main.min.css"
        assets_ignore = r".*\.map|css/_.*"
        if built_css.exists():
            external_stylesheets.append("/assets/dist/main.min.css")
            assets_ignore += r"|css/main\.css"

        app = dash.Dash(
            __name__,
            external_stylesheets=external_stylesheets,
            suppress_callback_exceptions=True,
            assets_ignore=assets_ignore,
        )

        cache.init_app(app.server)
        app.cache = cache

        app.index_string = f"""
<!DOCTYPE html>
<html>
  <head>
    {{%metas%}}
    <title>Yōsai Intel Dashboard</title>
    <link rel=\"stylesheet\" href=\"{BUNDLE}\" />
    {{%favicon%}}
    {{%css%}}
  </head>
  <body>
    {{%app_entry%}}
    <footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer>
  </body>
</html>
"""

        apply_theme_settings(app)
        Compress(app.server)
        cfg = get_config()
        https_only = cfg.get_app_config().environment == "production"
        Talisman(
            app.server,
            content_security_policy=None,
            force_https=https_only,
            force_https_permanent=https_only,
        )

        @app.server.after_request  # type: ignore[misc]
        def add_cache_headers(resp):
            if resp.mimetype and resp.mimetype.startswith(
                ("text/", "application/javascript", "image/")
            ):
                resp.headers["Cache-Control"] = "public,max-age=31536000,immutable"
            return resp

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
    theme = sanitize_theme(os.getenv("YOSAI_THEME", DEFAULT_THEME))
    return html.Div(
        [
            # URL routing component
            dcc.Location(id="url", refresh=False),
            # Navigation bar wrapped in semantic <nav> element
            html.Nav(
                _create_navbar(),
                className="top-panel",
            ),
            # Main content area (dynamically populated)
            dcc.Loading(
                id="page-loading",
                type="circle",
                children=html.Main(id="page-content", className="main-content p-4"),
            ),
            # Global data stores
            dcc.Store(id="global-store", data={}),
            dcc.Store(id="session-store", data={}),
            dcc.Store(id="app-state-store", data={"initial": True}),
            dcc.Store(id="theme-store", data=DEFAULT_THEME),
            html.Div(id="theme-dummy-output", style={"display": "none"}),
        ],
        **{"data-theme": theme},
    )


def _create_navbar() -> dbc.Navbar:
    """Wrapper to create the navigation bar layout."""
    return create_navbar_layout()


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


def _register_router_callbacks(manager: TrulyUnifiedCallbacks) -> None:
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
        elif pathname == "/export":
            return _get_export_page()
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
    """Get default home page."""
    return _get_analytics_page()


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


def _get_export_page() -> Any:
    """Get export page."""
    try:
        from pages.export import layout

        return layout()
    except ImportError as e:
        logger.error(f"Export page import failed: {e}")
        return _create_placeholder_page(
            "Export",
            "Export page is being loaded...",
            "The export module is not available. Please check the installation.",
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


def _register_global_callbacks(manager: TrulyUnifiedCallbacks) -> None:
    """Register global application callbacks"""

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
    try:
        server.config.setdefault("SWAGGER", {"uiversion": 3})
        template = {
            "openapi": "3.0.2",
            "info": {
                "title": "Yōsai Intel Dashboard API",
                "version": "1.0.0",
            },
        }
        Swagger(server, template=template)
        logger.info("✅ Swagger configured successfully")
    except Exception as e:
        logger.warning(f"Swagger configuration failed, continuing without it: {e}")
        # Don't crash the app if Swagger fails


# Export the main function
__all__ = ["create_app"]
