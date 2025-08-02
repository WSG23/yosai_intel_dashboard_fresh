#!/usr/bin/env python
from __future__ import annotations

import logging
import os
import sys

from yosai_intel_dashboard.src.core.env_validation import validate_required_env

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app directly from adapter
from api.adapter import create_api_app
from yosai_intel_dashboard.src.core.di.bootstrap import bootstrap_container

# Import Dash app factory from the package
from yosai_intel_dashboard.src.core.app_factory import create_app
from yosai_intel_dashboard.src.infrastructure.config.constants import API_PORT


def main() -> None:
    """Start the API development server."""
    validate_required_env()
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
