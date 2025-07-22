#!/usr/bin/env python3
"""Fresh, minimal app factory."""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

# Import Path for building robust file paths
from components.ui.navbar import create_navbar_layout


def create_app(mode=None, **kwargs):
    """Create a working Dash app with logo, navigation, and routing - HTTPS ready."""

    app = dash.Dash(
        __name__,
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

    app.title = "🏯 Yōsai Intel Dashboard"
    return app
