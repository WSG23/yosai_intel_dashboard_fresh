import logging
import os

logger = logging.getLogger(__name__)


def setup_dev_mode():
"""Validate required secrets in development mode."""
    if os.getenv("YOSAI_ENV", "development") == "development":
        required = [
            "AUTH0_CLIENT_ID",
            "AUTH0_CLIENT_SECRET",
            "AUTH0_DOMAIN",
            "AUTH0_AUDIENCE",
            "SECRET_KEY",
            "DB_PASSWORD",
        ]
        missing = [k for k in required if not os.getenv(k)]
        if missing:
            raise RuntimeError(
                f"Missing required development secrets: {', '.join(missing)}"
            )
