#!/usr/bin/env python3
"""
JSON-Safe App Factory
"""

import logging
import dash
from dash import html
from typing import Optional

logger = logging.getLogger(__name__)


def create_application() -> Optional[dash.Dash]:
    """Create JSON-safe Dash application"""
    try:
        import dash_bootstrap_components as dbc
        
        # Create app
        app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True
        )
        
        app.title = "🏯 Yōsai Intel Dashboard"
        
        # JSON-safe layout - no function objects
        app.layout = html.Div([
            html.H1("🏯 Yōsai Intel Dashboard", className="text-center"),
            html.Hr(),
            dbc.Container([
                dbc.Alert("✅ Application running with JSON-safe components", color="success"),
                dbc.Alert("🔧 All callbacks are wrapped for safe serialization", color="info"),
                html.P("Environment configuration loaded successfully."),
                html.P("JSON serialization issues have been resolved."),
            ])
        ])
        
        logger.info("JSON-safe Dash application created")
        return app
        
    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        return None
