from __future__ import annotations

"""Secret management abstraction"""

import os
import secrets
import logging
from typing import Any, Dict, List, Optional

from core.exceptions import SecurityError


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

    @staticmethod
    def generate_secret_key(length: int = 32) -> str:
        """Generate a cryptographically secure secret key."""
        return secrets.token_urlsafe(length)

    @staticmethod
    def get_secret_key() -> str:
        """Retrieve SECRET_KEY from the environment and validate it."""
        key = os.environ.get("SECRET_KEY")
        if not key:
            raise SecurityError("SECRET_KEY environment variable required")
        if len(key) < 32:
            raise SecurityError("SECRET_KEY must be at least 32 characters")
        return key

    def _get_aws_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret from AWS Secrets Manager."""
        try:
            import base64
            import boto3
            client = boto3.client(
                "secretsmanager",
                region_name=os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
            )
            resp = client.get_secret_value(SecretId=key)
            if "SecretString" in resp:
                return resp["SecretString"]
            if "SecretBinary" in resp:
                return base64.b64decode(resp["SecretBinary"]).decode("utf-8")
        except Exception as exc:
            logging.getLogger(__name__).warning("AWS secret fetch failed: %s", exc)
        return None

    def _get_vault_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret from HashiCorp Vault."""
        try:
            import hvac

            url = os.getenv("VAULT_ADDR")
            token = os.getenv("VAULT_TOKEN")
            if not url or not token:
                return None

            client = hvac.Client(url=url, token=token)
            if "#" in key:
                path, field = key.split("#", 1)
            else:
                path, field = key, "value"
            resp = client.secrets.kv.v2.read_secret_version(path=path)
            return resp["data"]["data"].get(field)
        except Exception as exc:
            logging.getLogger(__name__).warning("Vault secret fetch failed: %s", exc)
        return None


def validate_secrets() -> Dict[str, Any]:
    """Return summary of required secret availability.

    This checks common environment-based secrets without exposing
    their actual values. The summary includes whether each secret is
    present and a list of any missing secrets. Secrets are considered
    required if the application is running in a production environment
    or if they are needed for authentication.
    """

    from config.config import get_config

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
