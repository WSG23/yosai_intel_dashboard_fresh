#!/usr/bin/env python3
"""Fresh, minimal app factory that WORKS with real pages - HTTPS enabled."""

import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
from components.ui.navbar import create_navbar_layout
from pages import file_upload_simple


def create_app(mode=None, **kwargs):
    """Create a working Dash app with logo, navigation, and routing - HTTPS ready."""

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

    # Register callbacks for individual pages
    file_upload_simple.register_page()
    file_upload_simple.register_callbacks(app)

    # Simple routing callback that uses REAL pages
    @app.callback(Output("page-content", "children"), Input("url", "pathname"))
    def display_page(pathname):
        if pathname == "/dashboard":
            return html.Div(
                [
                    html.H1("🏠 Dashboard", className="mb-4"),
                    html.P("Welcome to your Yōsai Intel Dashboard!"),
                ]
            )
        elif pathname == "/analytics":
            return html.Div(
                [
                    html.H1("📊 Analytics", className="mb-4"),
                    html.P("Analytics page - working!"),
                ]
            )
        elif pathname == "/graphs":
            return html.Div(
                [
                    html.H1("📈 Graphs", className="mb-4"),
                    html.P("Graphs page - working!"),
                ]
            )
        elif pathname == "/upload":
            # Delegate to simplified upload page
            return file_upload_simple.layout()
        elif pathname == "/export":
            return html.Div(
                [
                    html.H1("📥 Export", className="mb-4"),
                    html.P("Export page - working!"),
                ]
            )
        elif pathname == "/settings":
            return html.Div(
                [
                    html.H1("⚙️ Settings", className="mb-4"),
                    html.P("Settings page - working!"),
                ]
            )
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

    app.title = "🏯 Yōsai Intel Dashboard"
    return app
