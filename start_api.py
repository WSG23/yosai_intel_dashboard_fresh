#!/usr/bin/env python
import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app directly from adapter
from api.adapter import create_api_app
from config.constants import API_PORT

logger = logging.getLogger("start")
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter(
        '{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}'
    )
)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def main() -> None:
    """Start the API development server."""
    app = create_api_app()

    print("\n🚀 Starting Yosai Intel Dashboard API...")
    print(f"   Available at: http://localhost:{API_PORT}")
    print(f"   Health check: http://localhost:{API_PORT}/v1/health")


    app.run(host="0.0.0.0", port=API_PORT, debug=True)


if __name__ == "__main__":
    main()
