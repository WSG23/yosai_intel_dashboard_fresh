import os
import logging

logger = logging.getLogger(__name__)


def setup_dev_mode() -> None:
    """Warn about missing secrets and optionally load test defaults."""

    env = os.getenv("YOSAI_ENV", "development").lower()

    defaults = {
        "AUTH0_CLIENT_ID": "test-client-id",
        "AUTH0_CLIENT_SECRET": "test-secret",
        "AUTH0_DOMAIN": "test.auth0.com",
        "AUTH0_AUDIENCE": "test-audience",
        "SECRET_KEY": "test-secret-key",
        "DB_PASSWORD": "test-password",
    }

    for key, value in defaults.items():
        if os.getenv(key):
            continue

        if env == "test":
            os.environ[key] = value
            logger.info("\ud83d\udd27 Loaded test default: %s", key)
        else:
            logger.warning(
                "Environment variable %s is not set; application may fail", key
            )


