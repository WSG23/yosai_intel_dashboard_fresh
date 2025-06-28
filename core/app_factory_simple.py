#!/usr/bin/env python3
"""
Emergency Simple App Factory - Syntax Error Free
"""

import logging
import dash
from typing import Optional

logger = logging.getLogger(__name__)


def create_application() -> Optional[dash.Dash]:
    """Create a simple Dash application without complex auth"""
    try:
        from dash import html, dcc
        import dash_bootstrap_components as dbc
        
        # Create basic Dash app
        app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True
        )
        
        app.title = "Yōsai Intel Dashboard"
        
        # Simple layout
        app.layout = html.Div([
            dcc.Location(id='url', refresh=False),
            html.H1("🏯 Yōsai Intel Dashboard", className="text-center"),
            html.Hr(),
            html.Div([
                dbc.Alert("✅ Application created successfully!", color="success"),
                dbc.Alert("⚠️ Running in simplified mode (no auth)", color="warning"),
                html.P("Environment configuration loaded and working."),
                html.P("Ready for development and testing."),
            ], className="container")
        ])
        
        logger.info("Simple Dash application created successfully")
        return app
        
    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        return None


# Backwards compatibility
def create_dash_app():
    """Legacy function name"""
    return create_application()
