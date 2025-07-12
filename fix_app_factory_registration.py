#!/usr/bin/env python3
"""Fix app factory page registration timing"""

# The issue is in core/app_factory/__init__.py in create_app()
# Page registration happens BEFORE app creation, but dash.register_page() needs the app to exist

# ORIGINAL BROKEN CODE (around line where register_pages() is called):
# register_pages()  # Called too early!
# app = dash.Dash(...)

# FIXED VERSION - Move page registration AFTER app creation:

def create_app_fixed_version():
    # 1. Create app first
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    
    # 2. THEN register pages (after app exists)
    try:
        from pages import register_pages
        register_pages()
        logger.info("✅ Pages registered successfully")
    except Exception as e:
        logger.warning(f"Page registration failed: {e}")
    
    # 3. Continue with rest of app setup...
    
# You need to move the register_pages() call to AFTER app = dash.Dash(...) in create_app()
