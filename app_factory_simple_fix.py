"""Simplified application factory used in tests and examples."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, cast

import dash
html = dash.html
dcc = dash.dcc
import dash_bootstrap_components as dbc
from flask import Flask
from flask_caching import Cache

from core.theme_manager import apply_theme_settings
from utils.assets_utils import fix_flask_mime_types, ensure_icon_cache_headers
from core.app_factory.health import register_health_endpoints


ASSETS_DIR = Path(__file__).resolve().parent / "assets"
BUNDLE = "/assets/dist/main.min.css"

logger = logging.getLogger(__name__)


class DummyConfigManager:
    """Minimal stand-in configuration manager."""

    def get_plugin_config(self, name: str) -> dict[str, Any]:
        return {}


def _register_callbacks(app: dash.Dash, config_manager: Any, container: Any | None = None) -> None:
    """Placeholder callback registration used in simplified mode."""
    logger.info("Registering callbacks (simplified)")


def _configure_swagger(server: Any) -> None:
    """Minimal Swagger configuration for development."""
    try:
        from flasgger import Swagger

        server.config.setdefault("SWAGGER", {"uiversion": 3})
        Swagger(server, template={"openapi": "3.0.2", "info": {"title": "Yōsai Intel Dashboard API", "version": "1.0.0"}})
        logger.info("✅ Swagger configured successfully")
    except Exception as e:  # pragma: no cover - best effort
        logger.warning(f"Swagger configuration failed: {e}")


def _create_simple_app(assets_folder: str) -> dash.Dash:
    """Create simple Dash application for development"""
    try:

        external_stylesheets = [dbc.themes.BOOTSTRAP]
        built_css = ASSETS_DIR / "dist" / "main.min.css"
        assets_ignore = r".*\.map|css/_.*"
        if built_css.exists():
            external_stylesheets.append("/assets/dist/main.min.css")
            assets_ignore += r"|css/main\.css"

        # ✅ FIXED: Create app FIRST
        app = dash.Dash(
            __name__,
            external_stylesheets=external_stylesheets,
            suppress_callback_exceptions=True,
            assets_folder=assets_folder,
            assets_ignore=assets_ignore,
            use_pages=True,
            pages_folder="",
        )
        
        # ✅ FIXED: THEN register pages (after app exists)
        try:
            from pages import register_pages
            register_pages()
            logger.info("✅ Pages registered successfully")
        except Exception as e:
            logger.warning(f"Page registration failed: {e}")

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

        # ✅ ENSURE page-content div exists in layout
        app.layout = html.Div([
            dcc.Location(id="url", refresh=False),
            html.H1("🏯 Yōsai Intel Dashboard", className="text-center"),
            html.Hr(),
            html.Div(id="page-content"),  # ✅ This is essential for routing!
            html.Div([
                dbc.Alert("✅ Application created successfully!", color="success"),
                dbc.Alert("⚠️ Running in simplified mode (no auth)", color="warning"),
                html.P("Environment configuration loaded and working."),
                html.P("Ready for development and testing."),
            ], className="container"),
        ])

        # Register callbacks after everything is set up
        config_manager = DummyConfigManager()
        _register_callbacks(app, config_manager, container=None)

        server = cast(Flask, app.server)
        _configure_swagger(server)
        register_health_endpoints(server)

        logger.info("Simple Dash application created successfully")
        return app

    except Exception as e:
        logger.error(f"Failed to create simple application: {e}")
        raise
