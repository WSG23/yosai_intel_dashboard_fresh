from __future__ import annotations

"""Secret management abstraction"""

import os
from typing import Optional


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


__all__ = ["SecretManager"]
