import logging
import os
import warnings

logger = logging.getLogger(__name__)


def setup_dev_mode():
    """Validate required secrets in development mode."""
    if os.getenv("YOSAI_ENV", "development") == "development":
        warnings.simplefilter("default", DeprecationWarning)
        required = [
            "AUTH0_CLIENT_ID",
            "AUTH0_CLIENT_SECRET",
            "AUTH0_DOMAIN",
            "AUTH0_AUDIENCE",
            "SECRET_KEY",
            "DB_PASSWORD",
        ]

        missing = [key for key in required if not os.getenv(key)]
        if missing:
            logger.warning(f"Missing environment variables: {missing}")
            logger.warning(
                "Run `cp .env.example .env` and `python scripts/generate_dev_secrets.py >> .env` "
                "to create default secrets."
            )
