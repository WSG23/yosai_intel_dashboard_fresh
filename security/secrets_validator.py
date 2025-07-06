import math
import re
from collections import Counter
from typing import Dict, List, Optional

from core.secrets_manager import SecretsManager


class SecretsValidator:
    """Validate application secrets for strength and patterns."""

    DEFAULT_PATTERNS = [
        re.compile(p, re.IGNORECASE)
        for p in ["dev", "development", "test", "secret", "change[-_]?me"]
    ]
    MIN_ENTROPY = 3.5

    def __init__(self, manager: Optional[SecretsManager] = None) -> None:
        self.manager = manager or SecretsManager()

    @staticmethod
    def _entropy(value: str) -> float:
        if not value:
            return 0.0
        length = len(value)
        counts = Counter(value)
        return -sum((c / length) * math.log2(c / length) for c in counts.values())

    def validate_secret(
        self, secret: str, environment: str = "development"
    ) -> Dict[str, List[str] | float]:
        warnings: List[str] = []
        errors: List[str] = []

        entropy = self._entropy(secret)

        if not secret:
            msg = "Secret missing"
            (errors if environment == "production" else warnings).append(msg)
        else:
            if any(p.search(secret) for p in self.DEFAULT_PATTERNS):
                msg = "Secret matches insecure pattern"
                (errors if environment == "production" else warnings).append(msg)
            if entropy < self.MIN_ENTROPY:
                msg = "Secret entropy too low"
                (errors if environment == "production" else warnings).append(msg)

        return {"warnings": warnings, "errors": errors, "entropy": entropy}


def register_health_endpoint(app, validator: Optional[SecretsValidator] = None) -> None:
    """Register /health/secrets endpoint on a Flask or Dash app."""
    validator = validator or SecretsValidator()
    server = app.server if hasattr(app, "server") else app

    @server.route("/health/secrets", methods=["GET"])
    def secrets_health():
        env = server.config.get("ENV", "development")
        secret = server.config.get("SECRET_KEY", "")
        result = validator.validate_secret(secret, environment=env)
        status = 200 if not result["errors"] else 500
        return result, status


__all__ = ["SecretsValidator", "register_health_endpoint"]
