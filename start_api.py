#!/usr/bin/env python
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app directly from adapter
import api.adapter

if __name__ == "__main__":
    # Get the app instance
    app = api.adapter.app
    
    print("\n🚀 Starting Yosai Intel Dashboard API...")
    print("   Available at: http://localhost:5001")
    print("   Health check: http://localhost:5001/api/v1/health")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
