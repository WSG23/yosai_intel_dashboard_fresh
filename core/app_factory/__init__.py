from components.ui.navbar import create_navbar_layout
#!/usr/bin/env python3
"""Minimal working app factory."""

import os
import logging
from dash import Dash, html, dcc
from components.ui.navbar import create_navbar_layout
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)

def _create_main_layout():
    """Create minimal working layout."""
    return html.Div([
        dcc.Location(id="url", refresh=False),
        create_navbar_layout(),
        html.Div(
            id="page-content",
            style={"paddingTop": "80px", "padding": "20px"},
            children=[
                dbc.Container([
                    html.H1("🚀 Loading Dashboard..."),
                    html.P("Manual routing should populate this area momentarily."),
                ])
            ],
        ),
        dcc.Store(id="global-store", data={}),
    ])

def create_app(mode=None, **kwargs):
    """Create minimal working app."""
    try:
        print('🔍 DEBUG: About to create Dash app...')
        app = Dash(__name__, assets_folder="/Users/tombrayman/Projects/GitHub/yosai_intel_dashboard_fresh/assets", external_stylesheets=[dbc.themes.BOOTSTRAP, "/assets/css/main.css"])
        
        # Set up layout as function
        app.layout = _create_main_layout
        
        # Register manual routing
        from pages import create_manual_router
        create_manual_router(app)
        
        logger.info("✅ Minimal app created with working layout and routing")
        return app
    except Exception as e:
        logger.error(f"❌ App creation failed: {e}")
        raise

# Add manual routing for page content
def add_manual_routing(app):
    """Add manual routing to display page content."""
    from pages import create_manual_router
    create_manual_router(app)
    logger.info("✅ Manual routing enabled")
