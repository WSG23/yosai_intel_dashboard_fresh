"""Configuration transformation utilities."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import Config

from .protocols import ConfigTransformerProtocol
from .env_overrides import apply_env_overrides

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
        apply_env_overrides(config)

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
                    f"postgresql://{config.database.user}:{config.database.password}",
                    f"@{config.database.host}:{config.database.port}",
                    f"/{config.database.name}",
                ]
                config.database.url = "".join(url_parts)


__all__ = ["ConfigTransformer"]
