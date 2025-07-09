"""Configuration transformation utilities."""

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import Config

from .protocols import ConfigTransformerProtocol

logger = logging.getLogger(__name__)


class ConfigTransformer(ConfigTransformerProtocol):
    """Transform and enhance configuration objects."""

    def transform(self, config: "Config") -> "Config":
        """Apply transformations to configuration object."""
        self._apply_environment_overrides(config)
        self._apply_security_defaults(config)
        self._apply_derived_values(config)
        return config

    def _apply_environment_overrides(self, config: "Config") -> None:
        """Apply environment variable overrides."""
        # App overrides
        if host := os.getenv("YOSAI_HOST"):
            config.app.host = host
        if port := os.getenv("YOSAI_PORT"):
            try:
                config.app.port = int(port)
            except ValueError:
                logger.warning("Invalid YOSAI_PORT value: %s", port)
        if debug := os.getenv("YOSAI_DEBUG"):
            config.app.debug = debug.lower() in ("true", "1", "yes")
        if secret := os.getenv("SECRET_KEY"):
            config.app.secret_key = secret

        # Database overrides
        if db_url := os.getenv("DATABASE_URL"):
            config.database.url = db_url
        if db_name := os.getenv("DB_NAME"):
            config.database.name = db_name
        if db_host := os.getenv("DB_HOST"):
            config.database.host = db_host
        if db_port := os.getenv("DB_PORT"):
            try:
                config.database.port = int(db_port)
            except ValueError:
                logger.warning("Invalid DB_PORT value: %s", db_port)
        if db_user := os.getenv("DB_USER"):
            config.database.username = db_user
        if db_pass := os.getenv("DB_PASSWORD"):
            config.database.password = db_pass

        # Security overrides
        if max_upload := os.getenv("MAX_UPLOAD_MB"):
            try:
                config.security.max_upload_mb = int(max_upload)
            except ValueError:
                logger.warning("Invalid MAX_UPLOAD_MB value: %s", max_upload)

    def _apply_security_defaults(self, config: "Config") -> None:
        """Apply security-related defaults."""
        # Ensure secret key is set
        if not config.app.secret_key or config.app.secret_key == "change-me":
            if config.environment == "production":
                logger.error("SECRET_KEY must be set in production")
            else:
                config.app.secret_key = "dev-key-change-in-production"

        # Set reasonable upload limits
        if config.security.max_upload_mb <= 0:
            config.security.max_upload_mb = 50

    def _apply_derived_values(self, config: "Config") -> None:
        """Calculate derived configuration values."""
        # Database URL construction if not explicitly set
        if not config.database.url and config.database.type != "sqlite":
            if config.database.type == "postgresql":
                url_parts = [
                    f"postgresql://{config.database.username}:{config.database.password}",
                    f"@{config.database.host}:{config.database.port}",
                    f"/{config.database.name}",
                ]
                config.database.url = "".join(url_parts)


__all__ = ["ConfigTransformer"]
