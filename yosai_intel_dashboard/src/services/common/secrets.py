from __future__ import annotations

import os
from typing import Optional

from yosai_intel_dashboard.src.infrastructure.config.environment import get_environment

from .vault_client import VaultClient


def _init_client() -> VaultClient:
    env = get_environment()
    addr = os.getenv("VAULT_ADDR")
    token = os.getenv("VAULT_TOKEN")

    if env == "development":
        addr = addr or "http://127.0.0.1:8200"

    if not addr or not token:
        raise RuntimeError("VAULT_ADDR and VAULT_TOKEN must be set")

    return VaultClient(url=addr, token=token)


_vault = _init_client()


def get_secret(key: str) -> str:
    """Return the secret value for *key* or raise RuntimeError if missing."""
    path, field = (key.split("#", 1) + [None])[:2]
    value = _vault.get_secret(path, field)
    if value is None:
        raise RuntimeError(f"secret {key} not found")
    return value  # type: ignore[return-value]


def invalidate_secret(key: Optional[str] = None) -> None:
    """Invalidate cached secrets."""
    _vault.invalidate(key)


__all__ = ["get_secret", "invalidate_secret"]
