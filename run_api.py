import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.adapter import app

if __name__ == "__main__":
    print("\n🚀 Starting Yosai Intel Dashboard API...")
    print("   Available at: http://localhost:5001")
    print("   Health check: http://localhost:5001/api/v1/health")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
