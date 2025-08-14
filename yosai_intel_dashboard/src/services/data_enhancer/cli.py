from __future__ import annotations

import logging

from yosai_intel_dashboard.src.core.logging import get_logger
from .app import create_standalone_app
from .config import (
    AI_COLUMN_SERVICE_AVAILABLE,
    AI_DOOR_SERVICE_AVAILABLE,
    CONFIG_SERVICE_AVAILABLE,
    CONTAINER_AVAILABLE,
)

logger = get_logger(__name__)


def run_data_enhancer() -> None:
    """Run the standalone data enhancer Dash application."""
    logging.basicConfig(level=logging.INFO)

    logger.info("=" * 70)
    logger.info("🚀 Starting MVP Data Enhancement Tool - Multi-Building Analysis")
    logger.info("=" * 70)
    logger.info(
        "Service availability",
        extra={
            "ai_column_service": AI_COLUMN_SERVICE_AVAILABLE,
            "ai_door_service": AI_DOOR_SERVICE_AVAILABLE,
            "config_service": CONFIG_SERVICE_AVAILABLE,
            "service_container": CONTAINER_AVAILABLE,
        },
    )
    logger.info("=" * 70)

    app = create_standalone_app()
    from .callbacks import register_callbacks

    register_callbacks(app, getattr(app, "_service_container", None))
    logger.info(
        "Running data enhancer server",
        extra={"host": "0.0.0.0", "port": 5003},
    )
    app.run_server(debug=True, host="0.0.0.0", port=5003)
