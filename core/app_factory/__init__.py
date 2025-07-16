#!/usr/bin/env python3
"""Fresh, minimal app factory that WORKS with real pages - HTTPS enabled."""

import dash
from dash import html, dcc, page_container
import dash_bootstrap_components as dbc
# Import Path for building robust file paths
from pathlib import Path
from components.ui.navbar import create_navbar_layout



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
            html.Div(page_container, id="page-content", className="main-content p-4"),
            dcc.Store(id="global-store", data={}),
        ]
    )

    app.title = "🏯 Yōsai Intel Dashboard"
    return app
