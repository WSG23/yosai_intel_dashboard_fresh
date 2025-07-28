#!/usr/bin/env python
import sys
import os
import logging

from core.env_validation import validate_env

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app directly from adapter
from api.adapter import create_api_app
from config.constants import API_PORT
from core.di.bootstrap import bootstrap_container

REQUIRED_ENV_VARS = [
    "SECRET_KEY",
    "DB_PASSWORD",
    "AUTH0_CLIENT_ID",
    "AUTH0_CLIENT_SECRET",
    "AUTH0_DOMAIN",
    "AUTH0_AUDIENCE",
    "JWT_SECRET",
]


def main() -> None:
    """Start the API development server."""
    validate_env(REQUIRED_ENV_VARS)
    container = bootstrap_container()
    app = create_api_app()
    # Expose the DI container on the FastAPI state for access by services
    app.state.container = container

    logger.info("\n🚀 Starting Yosai Intel Dashboard API...")
    logger.info(f"   Available at: http://localhost:{API_PORT}")
    logger.info(f"   Health check: http://localhost:{API_PORT}/health")

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=API_PORT)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
