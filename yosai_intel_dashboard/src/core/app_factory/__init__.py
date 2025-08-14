#!/usr/bin/env python3
"""Fresh, minimal app factory."""

import os

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

# Import Path for building robust file paths
try:
    from yosai_intel_dashboard.src.adapters.ui.components.ui.navbar import *  # type: ignore  # noqa: F403

    _NAVBAR_AVAILABLE = True
except Exception:
    _NAVBAR_AVAILABLE = False

from yosai_intel_dashboard.src.infrastructure.error_handling.handlers import (
    register_error_handlers,
)
from yosai_intel_dashboard.src.core.app_factory.health import (
    register_health_endpoints,
)


def create_app(mode=None, **kwargs):
    """Create a working Dash app with logo, navigation, and routing - HTTPS ready."""

    assets_external = os.environ.get("ASSET_CDN_URL")

    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        assets_url_path="/assets",
        assets_external_path=assets_external or None,
    )

    register_error_handlers(app.server)
    register_health_endpoints(app.server)

    # if navbar is optional, skip if missing
    if not _NAVBAR_AVAILABLE:
        # proceed without navbar; layout should still be created elsewhere
        navbar_layout = None
    else:
        navbar_layout = create_navbar_layout()  # noqa: F405

    # Simple working layout
    app.layout = html.Div(
        [
            dcc.Location(id="url", refresh=False),
            navbar_layout,
            html.Div(id="page-content", className="main-content p-4"),
            html.Div(id="global-store"),
        ]
    )

    app.title = "🏯 Yōsai Intel Dashboard"
    return app
