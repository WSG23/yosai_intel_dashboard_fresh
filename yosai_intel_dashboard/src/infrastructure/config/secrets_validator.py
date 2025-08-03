from __future__ import annotations

"""Secrets validation utilities."""

import hmac
import logging
import math
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SecretValidationResult:
    """Result of validating a secret."""

    is_valid: bool
    issues: List[str] = field(default_factory=list)
    severity: str = "info"
    recommendations: List[str] = field(default_factory=list)


class SecretSource:
    """Base class for secret providers."""

    def get_secret(self, key: str) -> Optional[str]:
        raise NotImplementedError


class EnvSecretSource(SecretSource):
    """Read secrets from environment variables."""

    def get_secret(self, key: str) -> Optional[str]:
        return os.getenv(key)


class DockerSecretSource(SecretSource):
    """Read secrets from files mounted by Docker."""

    def __init__(self, base_path: Path | str = "/run/secrets") -> None:
        self.base_path = Path(base_path)

    def get_secret(self, key: str) -> Optional[str]:
        try:
            with open(self.base_path / key, "r", encoding="utf-8") as fh:
                return fh.read().strip()
        except OSError:
            return None


class CloudSecretSource(SecretSource):
    """Placeholder for cloud secret backends."""

    def get_secret(self, key: str) -> Optional[str]:
        # Integration with AWS/GCP/Azure would go here
        return None


class SecretsValidator:
    """Validate secrets according to environment specific rules."""

    _entropy_threshold = 3.5
    REQUIRED_PRODUCTION_SECRETS = [
        "SECRET_KEY",
        "DB_PASSWORD",
        "AUTH0_CLIENT_SECRET",
    ]

    def __init__(self, environment: str = "development") -> None:
        self.environment = environment
        self.patterns = [re.compile(r"password", re.IGNORECASE)]
        self.forbidden_values = {"", "changeme", "default"}
        self.forbidden_prefixes = {"dev-", "test-"}

    @staticmethod
    def _shannon_entropy(data: str) -> float:
        if not data:
            return 0.0
        counts = Counter(data)
        entropy = -sum(
            (c / len(data)) * math.log2(c / len(data)) for c in counts.values()
        )
        return entropy

    def _check_entropy(self, secret: str, issues: List[str]) -> None:
        bits_per_char = self._shannon_entropy(secret)
        bits_per_char = bits_per_char / len(secret) if secret else 0
        if bits_per_char < self._entropy_threshold:
            issues.append("Secret entropy too low")

    def _check_patterns(self, secret: str, issues: List[str]) -> None:
        for pat in self.patterns:
            if pat.search(secret):
                issues.append("Secret matches insecure pattern")
                break

    def _check_forbidden(self, secret: str, issues: List[str]) -> None:
        for value in self.forbidden_values:
            if hmac.compare_digest(secret, value):
                issues.append("Secret is forbidden value")
                return
        for prefix in self.forbidden_prefixes:
            if secret.startswith(prefix):
                issues.append("Secret uses forbidden prefix")
                return

    def validate_secret(
        self, secret: str
    ) -> tuple[SecretValidationResult, Optional[str]]:
        """Validate ``secret`` and return the result and any generated secret.

        In development environments an insecure secret will be replaced with a
        newly generated value.  The caller may retrieve this value from the
        second element of the returned tuple.  For all other environments the
        second element will be ``None``.
        """

        issues: List[str] = []
        secret_bytes = bytearray(secret.encode())

        self._check_entropy(secret, issues)
        self._check_patterns(secret, issues)
        self._check_forbidden(secret, issues)

        recommendations = ["Rotate secret regularly"]
        severity = "info"
        is_valid = not issues
        generated: Optional[str] = None

        if not is_valid:
            severity = "high" if self.environment == "production" else "medium"
            if self.environment == "development":
                generated = self._generate_secret()
                secret = generated
                is_valid = True
                recommendations.append("Auto-generated development secret")
                issues.clear()
                severity = "info"
            elif self.environment == "staging":
                logger.warning("Secret validation issues: %s", ",".join(issues))

        for i in range(len(secret_bytes)):
            secret_bytes[i] = 0
        result = SecretValidationResult(is_valid, issues, severity, recommendations)
        return result, generated

    def validate_production_secrets(
        self, source: Optional[SecretSource] = None
    ) -> Dict[str, str]:
        """Validate critical secrets for a production environment.

        Raises a ``ValueError`` if any required secret is missing or insecure.
        """
        source = source or EnvSecretSource()
        missing: List[str] = []
        secrets: Dict[str, str] = {}
        for key in self.REQUIRED_PRODUCTION_SECRETS:
            value = source.get_secret(key)
            if not value or len(value) < 32 or value.startswith("test-"):
                missing.append(key)
            else:
                secrets[key] = value
        if missing:
            raise ValueError("Invalid production secrets: " + ", ".join(missing))
        return secrets

    @staticmethod
    def check_rotation_needed(last_rotated: datetime, rotation_days: int) -> bool:
        return datetime.utcnow() - last_rotated > timedelta(days=rotation_days)

    @staticmethod
    def _generate_secret(length: int = 32) -> str:
        import secrets

        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return "".join(secrets.choice(alphabet) for _ in range(length))


__all__ = [
    "SecretValidationResult",
    "SecretSource",
    "EnvSecretSource",
    "DockerSecretSource",
    "CloudSecretSource",
    "SecretsValidator",
]
