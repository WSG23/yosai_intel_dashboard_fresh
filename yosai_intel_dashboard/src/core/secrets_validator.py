from __future__ import annotations

"""Runtime secrets validation utilities."""

import logging
import os
from datetime import datetime
from typing import Dict, Optional

from yosai_intel_dashboard.src.core.exceptions import ConfigurationError

from .secret_manager import SecretsManager


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

    ROTATION_DAYS = {
        "SECRET_KEY": 90,
        "DB_PASSWORD": 30,
    }

    def __init__(self, manager: Optional[SecretsManager] = None) -> None:
        self.manager = manager or SecretsManager()
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
                if key == "SECRET_KEY":
                    try:
                        from yosai_intel_dashboard.src.infrastructure.config import (
                            get_security_config,
                        )

                        value = getattr(get_security_config(), "secret_key", None)
                    except Exception:  # pragma: no cover - best effort
                        value = None
                if not value:
                    try:  # pragma: no cover - best effort
                        from yosai_intel_dashboard.src.services.common.secrets import (
                            get_secret,
                        )

                        value = get_secret(key)
                    except Exception:
                        value = None
            if not value:
                missing.append(key)
            else:
                secrets[key] = value
        if missing:
            raise ConfigurationError(f"Missing required secrets: {', '.join(missing)}")
        return secrets

    def validate_production_secrets(self) -> list[str]:
        """Validate quality of secrets for production environment.

        Returns a list of secret keys that failed validation."""
        from yosai_intel_dashboard.src.infrastructure.security.secrets_validator import (
            SecretsValidator as QualityValidator,
        )

        secrets = self.validate_all_secrets()
        quality = QualityValidator()
        invalid: list[str] = []

        for name, value in secrets.items():
            result = quality.validate_secret(value, environment="production")
            if result["errors"]:
                invalid.append(name)

            rotation_days = self.ROTATION_DAYS.get(name)
            if rotation_days is not None:
                last_rotated_raw = os.getenv(f"{name}_LAST_ROTATED")
                if last_rotated_raw:
                    try:
                        last_rotated = datetime.fromisoformat(last_rotated_raw)
                    except ValueError:
                        invalid.append(name)
                    else:
                        if SecretsManager.needs_rotation(last_rotated, rotation_days):
                            invalid.append(name)

        return invalid


def validate_all_secrets(manager: Optional[SecretsManager] = None) -> Dict[str, str]:
    """Convenience wrapper for :class:`SecretsValidator`."""
    validator = SecretsValidator(manager)
    return validator.validate_all_secrets()


def validate_production_secrets(
    manager: Optional[SecretsManager] = None,
) -> list[str]:
    """Convenience wrapper for :meth:`SecretsValidator.validate_production_secrets`."""
    validator = SecretsValidator(manager)
    return validator.validate_production_secrets()


__all__ = [
    "SecretsValidator",
    "validate_all_secrets",
    "validate_production_secrets",
]
