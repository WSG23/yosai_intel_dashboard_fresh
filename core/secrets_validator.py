from __future__ import annotations

"""Runtime secrets validation utilities."""

import logging
from typing import Dict, Optional

from .secret_manager import SecretManager
from core.exceptions import ConfigurationError


class SecretsValidator:
    """Validate presence of required runtime secrets."""

    REQUIRED_SECRETS = [
        "SECRET_KEY",
        "DB_PASSWORD",
        "AUTH0_CLIENT_ID",
        "AUTH0_CLIENT_SECRET",
        "AUTH0_DOMAIN",
        "AUTH0_AUDIENCE",
    ]

    def __init__(self, manager: Optional[SecretManager] = None) -> None:
        self.manager = manager or SecretManager()
        self.logger = logging.getLogger(__name__)

    def validate_all_secrets(self) -> Dict[str, str]:
        """Ensure all required secrets are available."""
        secrets: Dict[str, str] = {}
        missing = []
        for key in self.REQUIRED_SECRETS:
            try:
                value = self.manager.get(key)
            except Exception:
                value = None
            if not value:
                missing.append(key)
            else:
                secrets[key] = value
        if missing:
            raise ConfigurationError(f"Missing required secrets: {', '.join(missing)}")
        return secrets


def validate_all_secrets(manager: Optional[SecretManager] = None) -> Dict[str, str]:
    """Convenience wrapper for :class:`SecretsValidator`."""
    validator = SecretsValidator(manager)
    return validator.validate_all_secrets()


__all__ = ["SecretsValidator", "validate_all_secrets"]
