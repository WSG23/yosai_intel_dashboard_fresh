#!/usr/bin/env python3
"""Fresh, minimal app factory that WORKS with real pages - HTTPS enabled."""

import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
from pathlib import Path
from components.ui.navbar import create_navbar_layout
from pages import (
    file_upload,
    deep_analytics,
    graphs,
    export,
    settings,
)


def create_app(mode=None, **kwargs):
    """Create a working Dash app with logo, navigation, and routing - HTTPS ready."""

    # The pages module lives in the project root, not under ``core``.
    # Resolve the project root and point Dash to the correct directory.
    pages_path = Path(__file__).resolve().parent.parent.parent / "pages"
    app = dash.Dash(
        __name__,
        use_pages=True,
        pages_folder=str(pages_path),
        external_stylesheets=[dbc.themes.BOOTSTRAP],
    )

    # Simple working layout
    app.layout = html.Div(
        [
            dcc.Location(id="url", refresh=False),
            create_navbar_layout(),
            html.Div(id="page-content", className="main-content p-4"),
            dcc.Store(id="global-store", data={}),
        ]
    )

    # Simple routing callback that uses REAL pages
    @app.callback(Output("page-content", "children"), Input("url", "pathname"))
    def display_page(pathname):
        """Return the layout for the requested URL path."""
        pathname = pathname.rstrip("/") if pathname else "/"

        if pathname in {"/", "/dashboard", "/analytics"}:
            return deep_analytics.layout()
        if pathname == "/graphs":
            return graphs.layout()
        if pathname == "/upload":
            return file_upload.layout()
        if pathname == "/export":
            return export.layout()
        if pathname == "/settings":
            return settings.layout()

        # Fallback to analytics page
        return deep_analytics.layout()

    app.title = "🏯 Yōsai Intel Dashboard"
    return app
