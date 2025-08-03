from __future__ import annotations

"""Unified secrets retrieval and management utilities."""

import os
import secrets
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional


@dataclass
class SecretMetadata:
    """Metadata describing a managed secret."""

    name: str
    required: bool = True
    min_length: int = 1
    rotation_days: Optional[int] = None


class SecretsManager:
    """Retrieve and rotate secrets from environment or Docker files."""

    def __init__(self, docker_dir: str | Path = "/run/secrets") -> None:
        """Initialize the manager with the directory holding Docker secrets."""
        self.docker_dir = Path(docker_dir)

    def _get_from_file(self, key: str) -> Optional[str]:
        try:
            with open(self.docker_dir / key, "r", encoding="utf-8") as fh:
                return fh.read().strip()
        except OSError:
            return None

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve a secret from environment or docker fallback."""
        value = os.getenv(key)
        if value is None:
            value = self._get_from_file(key)
        if value is None:
            value = default
        return value

    def validate(self, meta: SecretMetadata) -> bool:
        """Validate presence and length of a secret defined by metadata."""
        value = self.get(meta.name)
        if value is None:
            return not meta.required
        return len(value) >= meta.min_length

    @staticmethod
    def needs_rotation(last_rotated: datetime, rotation_days: int) -> bool:
        """Return True if the secret is older than ``rotation_days`` days."""
        return datetime.utcnow() - last_rotated > timedelta(days=rotation_days)

    def rotate_secret(self, key: str, length: int = 32) -> str:
        """Generate and store a new secret for the given key."""
        new_value = secrets.token_urlsafe(length)
        os.environ[key] = new_value
        return new_value


def validate_secrets(manager: Optional[SecretsManager] = None) -> dict[str, Any]:
    """Return summary of required secrets presence using the provided manager."""
    from yosai_intel_dashboard.src.infrastructure.config import get_config

    manager = manager or SecretsManager()
    config = get_config()
    env = config.get_app_config().environment

    required = ["SECRET_KEY"]
    if env == "production":
        required.append("DB_PASSWORD")

    optional = [
        "AUTH0_CLIENT_ID",
        "AUTH0_CLIENT_SECRET",
        "AUTH0_DOMAIN",
        "AUTH0_AUDIENCE",
    ]

    summary = {"environment": env, "checks": {}, "missing": []}
    for key in required + optional:
        value = manager.get(key)
        present = value is not None and value != ""
        summary["checks"][key] = present
        if key in required and not present:
            summary["missing"].append(key)

    summary["valid"] = len(summary["missing"]) == 0
    return summary


class SecretManager(SecretsManager):
    """Deprecated alias for :class:`SecretsManager`."""

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[override]
        warnings.warn(
            "SecretManager is deprecated; use SecretsManager",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


__all__ = ["SecretMetadata", "SecretsManager", "SecretManager", "validate_secrets"]
