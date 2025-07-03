import os
import logging

logger = logging.getLogger(__name__)


def setup_dev_mode():
    """Set development defaults for missing Auth0 secrets"""
    if os.getenv("YOSAI_ENV", "development") == "development":
        defaults = {
            "AUTH0_CLIENT_ID": "dev-client-id",
            "AUTH0_CLIENT_SECRET": "dev-secret",
            "AUTH0_DOMAIN": "dev.auth0.com",
            "AUTH0_AUDIENCE": "dev-audience",
            "SECRET_KEY": "dev-secret-key",
            "DB_PASSWORD": "dev-password",
        }
        for key, value in defaults.items():
            if not os.getenv(key):
                os.environ[key] = value
                logger.info(f"\ud83d\udd27 Set dev default: {key}")
