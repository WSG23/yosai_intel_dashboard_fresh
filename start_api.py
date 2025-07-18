#!/usr/bin/env python
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app directly from adapter
import api.adapter
from config.constants import API_PORT

if __name__ == "__main__":
    # Get the app instance
    app = api.adapter.app
    
    print("\n🚀 Starting Yosai Intel Dashboard API...")
    print(f"   Available at: http://localhost:{API_PORT}")
    print(f"   Health check: http://localhost:{API_PORT}/api/v1/health")

    app.run(host='0.0.0.0', port=API_PORT, debug=True)
