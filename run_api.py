import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.adapter import app
from config.constants import API_PORT

if __name__ == "__main__":
    print("\n🚀 Starting Yosai Intel Dashboard API...")
    print(f"   Available at: http://localhost:{API_PORT}")
    print(f"   Health check: http://localhost:{API_PORT}/api/v1/health")

    app.run(host='0.0.0.0', port=API_PORT, debug=True)
