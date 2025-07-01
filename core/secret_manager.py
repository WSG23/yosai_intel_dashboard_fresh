from __future__ import annotations

"""Secret management abstraction"""

import os
from typing import Optional, Dict, Any, List

from config.config import get_config


class SecretManager:
    """Retrieve secrets from various backends."""

    def __init__(self, backend: Optional[str] = None) -> None:
        self.backend = backend or os.getenv("SECRET_BACKEND", "env")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        if self.backend == "env":
            value = os.getenv(key, default)
        elif self.backend == "aws":
            value = self._get_aws_secret(key)
        elif self.backend == "vault":
            value = self._get_vault_secret(key)
        else:
            raise ValueError(f"Unsupported secret backend: {self.backend}")

        if value is None and default is None:
            raise KeyError(f"Secret '{key}' not found")
        return value

    def _get_aws_secret(self, key: str) -> Optional[str]:
        raise NotImplementedError("AWS secrets backend not configured")

    def _get_vault_secret(self, key: str) -> Optional[str]:
        raise NotImplementedError("Vault secrets backend not configured")


def validate_secrets() -> Dict[str, Any]:
    """Return summary of required secret availability.

    This checks common environment-based secrets without exposing
    their actual values. The summary includes whether each secret is
    present and a list of any missing secrets. Secrets are considered
    required if the application is running in a production environment
    or if they are needed for authentication.
    """

    config = get_config()
    env = config.get_app_config().environment

    required: List[str] = ["SECRET_KEY"]
    if env == "production":
        required.append("DB_PASSWORD")

    # Auth0 secrets are optional but included in the report
    optional = [
        "AUTH0_CLIENT_ID",
        "AUTH0_CLIENT_SECRET",
        "AUTH0_DOMAIN",
        "AUTH0_AUDIENCE",
    ]

    summary = {"environment": env, "checks": {}, "missing": []}

    for key in required + optional:
        value = os.getenv(key)
        present = value is not None and value != ""
        summary["checks"][key] = present
        if key in required and not present:
            summary["missing"].append(key)

    summary["valid"] = len(summary["missing"]) == 0
    return summary


__all__ = ["SecretManager", "validate_secrets"]
