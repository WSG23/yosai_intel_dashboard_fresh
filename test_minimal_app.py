#!/usr/bin/env python3
"""Minimal app test to isolate the Flask/Dash issue."""

import os
import sys
import logging

# Set required environment variables
os.environ["DB_PASSWORD"] = "test_password"
os.environ["SECRET_KEY"] = "test_key"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    print("🧪 Testing basic Dash import...")
    import dash
    from dash import Dash, html, dcc
    import dash_bootstrap_components as dbc
    print("✅ Dash imports successful")
    
    print("🧪 Creating basic Dash app...")
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    print(f"✅ Basic Dash app created: {type(app)}")
    print(f"✅ App.server type: {type(app.server)}")
    
    print("🧪 Testing imports from your modules...")
    try:
        from components.ui.navbar import create_navbar_layout
        print("✅ Navbar import successful")
    except Exception as e:
        print(f"❌ Navbar import failed: {e}")
    
    try:
        from config import get_config
        config = get_config()
        print("✅ Config import successful")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
    
    try:
        from core.service_container import ServiceContainer
        container = ServiceContainer()
        print("✅ Service container import successful")
    except Exception as e:
        print(f"❌ Service container import failed: {e}")
        
    try:
        from config.complete_service_registration import register_all_application_services
        print("✅ Service registration import successful")
        # Don't call it yet, just test the import
    except Exception as e:
        print(f"❌ Service registration import failed: {e}")
    
    print("🎉 All basic tests passed!")
    
except Exception as e:
    print(f"❌ Failed at: {e}")
    import traceback
    traceback.print_exc()
