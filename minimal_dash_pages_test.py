#!/usr/bin/env python3
"""Minimal Dash Pages test to isolate fundamental issues"""

import dash
from dash import html, dcc, page_container
import dash_bootstrap_components as dbc
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create minimal app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Register minimal test pages
dash.register_page("home", path="/", name="Home", layout=lambda: html.H1("🏠 HOME PAGE WORKS!"))
dash.register_page("test", path="/test", name="Test", layout=lambda: html.H1("✅ TEST PAGE WORKS!"))

# Simple app layout with page_container
app.layout = dbc.Container([
    html.H2("🧪 Minimal Dash Pages Test"),
    html.Hr(),
    dbc.Nav([
        dbc.NavLink("Home", href="/", active="exact"),
        dbc.NavLink("Test", href="/test", active="exact"),
    ], pills=True, className="mb-3"),
    
    # This is the key component - page_container
    page_container
], fluid=True)

def check_dash_pages_setup():
    """Check if Dash Pages is working correctly."""
    try:
        # Check if pages were registered
        pages = getattr(app, '_pages_data', {})
        logger.info(f"Registered pages: {list(pages.keys())}")
        
        # Check page_container
        logger.info(f"Page container available: {page_container is not None}")
        
        return True
    except Exception as e:
        logger.error(f"Dash Pages setup issue: {e}")
        return False

if __name__ == '__main__':
    print("🧪 Starting minimal Dash Pages test...")
    
    setup_ok = check_dash_pages_setup()
    if setup_ok:
        print("✅ Dash Pages setup appears correct")
    else:
        print("❌ Dash Pages setup has issues")
    
    print("\n🚀 Starting server on http://127.0.0.1:8051")
    print("📋 Test checklist:")
    print("   1. Visit http://127.0.0.1:8051/ - should show 'HOME PAGE WORKS!'")
    print("   2. Click 'Test' nav link - should show 'TEST PAGE WORKS!'") 
    print("   3. Try direct URL http://127.0.0.1:8051/test")
    print("   4. Check browser console for any JavaScript errors")
    print("\n🛑 Press Ctrl+C to stop")
    
    try:
        app.run_server(debug=True, port=8051, host='127.0.0.1')
    except KeyboardInterrupt:
        print("\n👋 Test stopped")
