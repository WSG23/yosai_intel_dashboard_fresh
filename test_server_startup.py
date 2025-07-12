#!/usr/bin/env python3
"""Test the exact server startup that causes the issue"""

print("🔍 Testing server startup process...")

try:
    from core.app_factory import create_app
    from pathlib import Path
    import os
    
    # Create app exactly like app.py does
    project_root = Path(__file__).resolve().parent
    assets_dir = os.path.normcase(os.path.abspath(project_root / "assets"))
    app = create_app(mode='full', assets_folder=assets_dir)
    
    print(f"✅ App created with {len(app._callback_list)} callbacks")
    
    # Test manual callback serialization (what /_dash-dependencies does)
    print("🔍 Testing callback serialization...")
    
    import json
    from dash._utils import to_json
    
    try:
        serialized = to_json(app._callback_list)
        print("✅ Callback serialization works!")
        print(f"Serialized length: {len(serialized)}")
    except Exception as e:
        print(f"❌ Callback serialization failed: {e}")
        import traceback
        traceback.print_exc()
        
    # Test starting server in non-blocking way
    print("🔍 Testing server startup...")
    
    # Start server without blocking (just test if it can start)
    import threading
    import time
    
    def start_server():
        try:
            app.run_server(debug=False, port=8052, host='127.0.0.1')
        except Exception as e:
            print(f"❌ Server startup failed: {e}")
    
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Give it a moment to start
    time.sleep(2)
    
    if server_thread.is_alive():
        print("✅ Server started successfully!")
        
        # Test the problematic endpoint
        import requests
        try:
            response = requests.get('http://127.0.0.1:8052/_dash-dependencies', timeout=5)
            print(f"✅ /_dash-dependencies returns: {response.status_code}")
        except Exception as e:
            print(f"❌ /_dash-dependencies failed: {e}")
    else:
        print("❌ Server failed to start")
        
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
