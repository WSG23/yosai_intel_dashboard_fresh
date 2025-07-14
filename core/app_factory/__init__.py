#!/usr/bin/env python3
"""Fresh, minimal app factory that WORKS."""

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html

from components.ui.navbar import create_navbar_layout
from pages.deep_analytics import AnalyticsPage
from pages.deep_analytics import layout as get_analytics_layout
from pages.export import layout as get_export_layout
from pages.file_upload import layout as get_upload_layout
from pages.graphs import layout as get_graphs_layout
from pages.settings import layout as get_settings_layout


def create_app(mode=None, **kwargs):
    """Create a working Dash app with logo, navigation, and routing."""

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    # Simple working layout
    app.layout = html.Div(
        [
            dcc.Location(id="url", refresh=False),
            create_navbar_layout(),
            html.Div(id="page-content", className="main-content p-4"),
            dcc.Store(id="global-store", data={}),
        ]
    )

    # Simple routing callback
    @app.callback(Output("page-content", "children"), Input("url", "pathname"))
    def display_page(pathname):
        if pathname in ("/dashboard", "/analytics"):
            try:
                return get_analytics_layout()
            except Exception as e:  # pragma: no cover - best effort fallback
                return html.Div(f"Error loading analytics page: {e}")
        elif pathname == "/upload":
            try:
                return get_upload_layout()
            except Exception as e:  # pragma: no cover
                return html.Div(f"Error loading upload page: {e}")
        elif pathname == "/graphs":
            try:
                return get_graphs_layout()
            except Exception as e:  # pragma: no cover
                return html.Div(f"Error loading graphs page: {e}")
        elif pathname == "/export":
            try:
                return get_export_layout()
            except Exception as e:  # pragma: no cover
                return html.Div(f"Error loading export page: {e}")
        elif pathname == "/settings":
            try:
                return get_settings_layout()
            except Exception as e:  # pragma: no cover
                return html.Div(f"Error loading settings page: {e}")
        else:
            return html.Div(
                [
                    html.H1("🏯 Yōsai Intel Dashboard", className="text-center mb-4"),
                    html.P(
                        "Select a page from the navigation menu above.",
                        className="text-center",
                    ),
                ]
            )

    analytics_page = AnalyticsPage()
    analytics_page.register_callbacks(app)

    app.title = "🏯 Yōsai Intel Dashboard"
    return app
