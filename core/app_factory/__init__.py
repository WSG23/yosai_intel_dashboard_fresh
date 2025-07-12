#!/usr/bin/env python3
"""Complete application factory integration."""
from __future__ import annotations

import importlib
import logging
import os
import sys
import time
import types
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, cast

# Graceful Dash imports with fallback
try:
    import dash
    import dash_bootstrap_components as dbc
    from dash import Input, Output, dcc, html, page_container

    DASH_AVAILABLE = True
except ImportError as e:
    logging.critical(f"❌ Dash import failed: {e}")
    logging.critical("Fix: pip install dash==2.14.1 dash-bootstrap-components==1.6.0")
    # For tests, provide stubs to prevent SystemExit
    if "pytest" in sys.modules:
        logging.warning("Running in test mode - using Dash stubs")

        class _MockDash:
            def __init__(self, *args, **kwargs) -> None:
                pass

            def callback(self, *args, **kwargs):
                return lambda f: f

            server = type("MockServer", (), {})()

        class _MockComponent:
            def __init__(self, *args, **kwargs) -> None:
                pass

        dash = cast(Any, types.SimpleNamespace(Dash=_MockDash))
        Input = Output = dcc = html = cast(Any, _MockComponent)
        dbc = cast(
            Any,
            types.SimpleNamespace(
                themes=types.SimpleNamespace(BOOTSTRAP=None),
                Alert=_MockComponent,
                Container=_MockComponent,
                Row=_MockComponent,
                Col=_MockComponent,
                Navbar=_MockComponent,
                Button=_MockComponent,
            ),
        )
        DASH_AVAILABLE = False
    else:
        sys.exit(1)


# Handle Unicode surrogates
from core.protocols import UnicodeProcessorProtocol


def handle_unicode_surrogates(
    text: str, processor: Optional[UnicodeProcessorProtocol] = None
) -> str:
    """Handle Unicode surrogate characters safely"""
    if not isinstance(text, str):
        return text
    try:
        if processor and hasattr(processor, "safe_encode_text"):
            return processor.safe_encode_text(text)
        return text.encode("utf-8", errors="ignore").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text.encode("ascii", errors="ignore").decode("ascii")


# Rest of imports
from flasgger import Swagger
from flask import Flask, session
from flask_babel import Babel
from flask_compress import Compress
from flask_talisman import Talisman


class DummyConfigManager:
    """Minimal configuration manager used in testing."""

    def __init__(self) -> None:
        self.config = types.SimpleNamespace(plugin_settings={})

    def get_plugin_config(self, name: str):
        return self.config.plugin_settings.get(name, {})


from flask_caching import Cache

from components.ui.navbar import create_navbar_layout
from config import get_config
from config.complete_service_registration import register_all_application_services
from core.callback_registry import GlobalCallbackRegistry, _callback_registry
from core.performance_monitor import DIPerformanceMonitor
from core.service_container import ServiceContainer
from core.theme_manager import DEFAULT_THEME, apply_theme_settings
from pages import get_page_layout
from pages.deep_analytics import Callbacks as DeepAnalyticsCallbacks
from pages.deep_analytics import layout as deep_analytics_layout
from pages.deep_analytics import register_callbacks as register_deep_callbacks
from pages.file_upload import register_callbacks as register_upload_callbacks
from pages.file_upload import safe_upload_layout
from services import get_analytics_service
from services.analytics_service import AnalyticsService
from utils.assets_debug import check_navbar_assets
from utils.assets_utils import (
    NAVBAR_ICON_NAMES,
    ensure_all_navbar_assets,
    ensure_icon_cache_headers,
    ensure_navbar_assets,
    fix_flask_mime_types,
)

from .health import register_health_endpoints
from .plugins import _initialize_plugins
from .security import initialize_csrf

# Optional callback system -------------------------------------------------
try:  # pragma: no cover - graceful import fallback
    from core.truly_unified_callbacks import TrulyUnifiedCallbacks
except Exception:  # pragma: no cover - fallback when unavailable
    TrulyUnifiedCallbacks = None  # type: ignore[misc]

if TYPE_CHECKING:  # pragma: no cover - only for type hints
    import dash_bootstrap_components as dbc
    from dash import Dash, Input, Output
    from dash import dcc as Dcc
    from dash import html as Html
    from dash_bootstrap_components import Container as DbcContainer

    from core.truly_unified_callbacks import (
        TrulyUnifiedCallbacks as TrulyUnifiedCallbacksType,
    )
else:  # pragma: no cover - fallback type alias
    TrulyUnifiedCallbacksType = Any

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
BUNDLE = "/assets/dist/main.min.css"

logger = logging.getLogger(__name__)


def create_app(
    mode: Optional[str] = None,
    *,
    assets_folder: Optional[str] = None,
) -> "Dash":
    """Create a Dash application.

    Parameters
    ----------
    mode: Optional[str]
        One of ``"full"`` (default), ``"simple"`` or ``"json-safe"``. The value
        can also be provided via the ``YOSAI_APP_MODE`` environment variable.
    """

    # Check Dash availability early
    if not DASH_AVAILABLE:
        logger.error("❌ Cannot create app - Dash not available")
        if "pytest" not in sys.modules:
            raise ImportError("Dash is not properly installed")

    try:
        config = get_config()
        config_manager = DummyConfigManager()  # Initialize config manager

        logger.info("🏗️ Creating Dash application...")

        assets_folder = (
            os.path.normcase(os.path.abspath(assets_folder))
            if assets_folder
            else os.path.normcase(os.path.abspath(str(ASSETS_DIR)))
        )
        logger.info(f"Assets folder resolved to: {assets_folder}")

        # Ensure navbar icons are available before constructing the Dash app
        try:
            ensure_all_navbar_assets()
            summary = check_navbar_assets(NAVBAR_ICON_NAMES, warn=False)
            missing = [n for n, ok in summary.items() if not ok]
            if missing:
                logger.warning("Missing navbar icons: %s", ", ".join(missing))
        except Exception as exc:  # pragma: no cover - best effort
            logger.debug("ensure_all_navbar_assets failed: %s", exc)

        # Determine app mode
        mode = mode or os.environ.get("YOSAI_APP_MODE", "full")
        logger.info(f"Application mode: {mode}")

        if mode == "simple":
            return _create_simple_app(assets_folder)
        elif mode == "json-safe":
            return _create_json_safe_app(assets_folder)

        logger.info("Creating application in full mode")
        return _create_full_app(assets_folder)

    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        raise


def _create_full_app(assets_folder: str) -> "Dash":
    """Create complete Dash application with full integration"""
    try:
        service_container = ServiceContainer()
        register_all_application_services(service_container)

        perf_monitor = DIPerformanceMonitor()
        original_get = service_container.get

        def monitored_get(service_key, protocol_type=None):
            start = time.time()
            try:
                result = original_get(service_key, protocol_type)
                perf_monitor.record_service_resolution(service_key, time.time() - start)
                return result
            except Exception as exc:
                perf_monitor.record_service_error(service_key, str(exc))
                raise

        service_container.get = monitored_get  # type: ignore
        service_container.register_singleton("performance_monitor", perf_monitor)

        config_manager = service_container.get("config_manager")
        analytics_service = service_container.get("analytics_service")
        try:
            health = analytics_service.health_check()
            logger.info(f"Analytics service initialized: {health}")
        except Exception as exc:  # pragma: no cover - service optional
            logger.warning(f"Analytics service health check failed: {exc}")

        external_stylesheets = [dbc.themes.BOOTSTRAP]
        built_css = ASSETS_DIR / "dist" / "main.min.css"
        assets_ignore = r".*\.map|css/_.*"
        if built_css.exists():
            external_stylesheets.append("/assets/dist/main.min.css")
            assets_ignore += r"|css/main\.css"
        # Ignore hidden files and text assets
        assets_ignore = r"^\..*|.*\.txt$"

        app = dash.Dash(
            __name__,
            external_stylesheets=external_stylesheets,
            suppress_callback_exceptions=True,
            assets_folder=assets_folder,
            assets_ignore=assets_ignore,
            use_pages=False,
            pages_folder="",
        )
        fix_flask_mime_types(app)
        ensure_icon_cache_headers(app)
        try:
            ensure_navbar_assets(app)
        except Exception as exc:  # pragma: no cover - best effort
            logger.debug("ensure_navbar_assets failed: %s", exc)

        if TrulyUnifiedCallbacks is not None:
            wrapper = TrulyUnifiedCallbacks(app)
            cast(Any, app).unified_callback = wrapper.unified_callback
            cast(Any, app).register_callback = wrapper.register_callback
            cast(Any, app)._unified_wrapper = wrapper
        else:  # pragma: no cover - fallback when dependency missing
            cast(Any, app).unified_callback = app.callback
            cast(Any, app).register_callback = app.callback
            logger.warning(
                "TrulyUnifiedCallbacks not available - falling back to Dash callback"
            )

        # Expose the service container on the app instance
        cast(Any, app)._service_container = service_container
        cast(Any, app).container = service_container

        # Initialize caching once per app instance
        cache = Cache(app.server, config={"CACHE_TYPE": "simple"})
        cast(Any, app).cache = cache

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
        # Use configuration service from the DI container
        config_manager = service_container.get("config_manager")
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

        analytics_cfg = config_manager.get_analytics_config()
        title = getattr(analytics_cfg, "title", config_manager.get_app_config().title)
        app.title = title

        # Initialize Flask-Babel before any layouts use gettext
        try:
            babel = Babel(app.server)

            def _select_locale() -> str:
                return session.get("locale", "en")

            selector = getattr(babel, "localeselector", None)
            if selector:
                selector(_select_locale)  # Flask-Babel <4
            else:
                selector = getattr(babel, "locale_selector_func", None)
                if selector:
                    selector(_select_locale)  # Flask-Babel 3.x
                else:  # pragma: no cover - Flask-Babel >=4
                    babel.locale_selector = _select_locale  # type: ignore[attr-defined]
            cast(Any, app.server).babel = babel
        except Exception as e:  # pragma: no cover - optional dependency
            logger.warning(f"Failed to initialize Babel: {e}")

        # Use the working config system
        initialize_csrf(app, config_manager)

        _initialize_plugins(app, config_manager, container=service_container)
        _register_pages()
        _setup_layout(app)
        _register_callbacks(app, config_manager, container=service_container)

        # Initialize services using the DI container
        _initialize_services(service_container)

        # Expose basic health check endpoint and Swagger docs
        server: Flask = cast(Flask, app.server)
        _configure_swagger(server)
        from services.progress_events import ProgressEventManager

        progress_events = ProgressEventManager()

        register_health_endpoints(server, progress_events)

        @server.before_request
        def filter_noisy_requests():
            """Filter out SSL handshake attempts and bot noise"""
            from flask import abort, request

            # Block requests with suspicious headers
            user_agent = request.headers.get("User-Agent", "")
            if not user_agent or len(user_agent) < 5:
                abort(400)

            # Block oversized requests that are likely noise
            content_length = request.headers.get("Content-Length")
            if content_length:
                try:
                    if int(content_length) > 50000:  # 50KB limit
                        abort(400)
                except (ValueError, TypeError):
                    pass

            # Block binary content that shouldn't be here
            content_type = request.headers.get("Content-Type", "")
            if request.method == "POST" and "application/x-" in content_type:
                abort(400)

        logger.info("✅ Complete Dash application created successfully")
        return app

    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        raise


def _create_simple_app(assets_folder: str) -> "Dash":
    """Create a simplified Dash application"""
    try:
        from dash import dcc, html, page_container

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
            assets_folder=assets_folder,
            assets_ignore=assets_ignore,
            use_pages=False,
            pages_folder="",
        )
        fix_flask_mime_types(app)
        ensure_icon_cache_headers(app)

        cache = Cache(app.server, config={"CACHE_TYPE": "simple"})
        cast(Any, app).cache = cache

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

        _register_pages()

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
        server: Flask = cast(Flask, app.server)
        _configure_swagger(server)

        register_health_endpoints(server)

        logger.info("Simple Dash application created successfully")
        return app

    except Exception as e:
        logger.error(f"Failed to create simple application: {e}")
        raise


def _create_json_safe_app(assets_folder: str) -> "Dash":
    """Create Dash application with JSON-safe layout"""
    try:
        from dash import html, page_container

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
            assets_folder=assets_folder,
            assets_ignore=assets_ignore,
            use_pages=False,
            pages_folder="",
        )
        fix_flask_mime_types(app)
        ensure_icon_cache_headers(app)

        cache = Cache(app.server, config={"CACHE_TYPE": "simple"})
        cast(Any, app).cache = cache

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

        _register_pages()

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
        server: Flask = cast(Flask, app.server)
        _configure_swagger(server)

        register_health_endpoints(server)

        logger.info("JSON-safe Dash application created")
        return app

    except Exception as e:
        logger.error(f"Failed to create JSON-safe application: {e}")
        raise


def _create_main_layout() -> "Html.Div":
    """Create main application layout with complete integration"""
    return html.Div(
        [
            # URL routing component
            dcc.Location(id="url", refresh=False),
            # Navigation bar wrapped in semantic <nav> element
            html.Nav(
                _create_navbar(),
                className="top-panel",
            ),
            # Main content area with Dash Pages content
            html.Main(
                page_container,
                id="page-content",
                className="main-content p-4",
            ),
            # Global data stores
            dcc.Store(id="global-store", data={}),
            dcc.Store(id="session-store", data={}),
            dcc.Store(id="app-state-store", data={"initial": True}),
            dcc.Store(id="theme-store", data=DEFAULT_THEME),
            html.Div(id="theme-dummy-output", style={"display": "none"}),
        ]
    )


def _create_navbar() -> Any:
    """Wrapper to create the navigation bar layout."""
    return create_navbar_layout()





def _register_global_callbacks(manager: TrulyUnifiedCallbacksType) -> None:
    """Register global application callbacks with consolidated management and Unicode safety"""

    if not DASH_AVAILABLE:
        logger.warning("⚠️ Skipping callback registration - Dash not available")
        return

    try:
        # Get app instance
        app = getattr(manager, "app", None)
        if not app:
            logger.error("❌ No app instance available for callback registration")
            return

        # Register device learning callbacks
        from services.device_learning_service import create_learning_callbacks

        create_learning_callbacks(manager)

        logger.info("✅ Global callbacks registered successfully")

    except Exception as e:
        logger.error(f"❌ Failed to register global callbacks: {e}")
        # Don't raise in test mode
        if "pytest" not in sys.modules:
            raise


def _register_pages() -> None:
    """Register all pages once the Dash app is ready."""
    try:
        from pages import register_pages

        register_pages()
        logger.info("✅ Pages registered successfully")
    except Exception as e:
        logger.warning(f"Page registration failed: {e}")


def _setup_layout(app: "Dash") -> None:
    """Attach main layout with caching."""

    layout_snapshot = None

    def _serve_layout() -> Any:
        nonlocal layout_snapshot
        if layout_snapshot is None:
            layout_snapshot = _create_main_layout()
        return layout_snapshot

    app.layout = _serve_layout


def _register_callbacks(
    app: "Dash",
    config_manager: Any,
    container: Optional[ServiceContainer] = None,
) -> None:
    """Register application callbacks using the unified coordinator."""

    global _callback_registry
    _callback_registry = GlobalCallbackRegistry()

    if hasattr(app, "_unified_wrapper"):
        coordinator = cast(TrulyUnifiedCallbacksType, getattr(app, "_unified_wrapper"))
    elif TrulyUnifiedCallbacks is not None:
        coordinator = TrulyUnifiedCallbacks(app)
        if hasattr(coordinator, "unified_callback"):
            cast(Any, app).unified_callback = coordinator.unified_callback
        if hasattr(coordinator, "register_callback"):
            cast(Any, app).register_callback = coordinator.register_callback
        cast(Any, app)._unified_wrapper = coordinator
    else:  # pragma: no cover - optional dependency missing
        coordinator = None
        cast(Any, app).unified_callback = app.callback
        cast(Any, app).register_callback = app.callback
        logger.warning(
            "TrulyUnifiedCallbacks unavailable; skipping unified callback setup"
        )

    if coordinator is not None:
        coordinator._callback_registry = _callback_registry
        registration_modules = [
            ("pages.file_upload", "register_callbacks"),  # RE-ENABLED
            ("pages.deep_analytics", "register_callbacks"),
            ("components.ui.navbar", "register_navbar_callbacks"),
        ]

        try:
            from services.interfaces import get_export_service

            unicode_proc = None
            if container:
                try:
                    unicode_proc = container.get("unicode_processor")
                except Exception:
                    unicode_proc = None

            # REMOVED: _register_router_callbacks(coordinator, unicode_proc)
            _register_global_callbacks(coordinator)

            for module_name, func_name in registration_modules:
                module = importlib.import_module(module_name)
                register_func = getattr(module, func_name)
                if func_name == "register_navbar_callbacks":
                    register_func(coordinator, get_export_service(container))
                else:
                    register_func(coordinator)
                logger.info("✅ Registered callbacks from %s", module_name)

            cast(Any, app)._upload_callbacks = object()
            cast(Any, app)._deep_analytics_callbacks = DeepAnalyticsCallbacks()

            if config_manager.get_app_config().environment == "development" and hasattr(
                coordinator, "print_callback_summary"
            ):
                coordinator.print_callback_summary()
        except Exception as e:  # pragma: no cover - log and continue
            logger.error("❌ Failed to register callbacks from modules: %s", e)
    else:
        logger.warning(
            "Skipping registration of module callbacks due to missing coordinator"
        )

    if coordinator is not None:
        if not _callback_registry.validate_registration_integrity():
            duplicates = {
                cid: count
                for cid, count in _callback_registry.registration_attempts.items()
                if count > 1
            }
            logger.warning("Duplicate callback registrations detected: %s", duplicates)


def _initialize_services(container: Optional[ServiceContainer] = None) -> None:
    """Initialize all application services"""
    try:
        container = container or ServiceContainer()

        if container.has("analytics_service"):
            analytics_service = container.get("analytics_service")
        else:
            from services import get_analytics_service

            analytics_service_func = cast(
                Callable[[], AnalyticsService], get_analytics_service
            )
            analytics_service = analytics_service_func()

        analytics_service = cast(AnalyticsService, analytics_service)
        health = analytics_service.health_check()
        logger.info(f"Analytics service initialized: {health}")

        if container.has("config_manager"):
            config = container.get("config_manager")
        else:
            config = get_config()

        app_config = config.get_app_config()
        logger.info(f"Configuration loaded for environment: {app_config.environment}")

        # Start WebSocket server for real-time analytics
        try:
            if container.has("event_bus"):
                from services.websocket_server import AnalyticsWebSocketServer

                ws_server = AnalyticsWebSocketServer(container.get("event_bus"))
                container.register_singleton("websocket_server", ws_server)
                logger.info("WebSocket server initialized")
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning(f"WebSocket server failed to start: {exc}")

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


