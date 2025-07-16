"""Config manager that fetches secrets from HashiCorp Vault."""

from __future__ import annotations

import logging
import os
from dataclasses import is_dataclass
from typing import Any, Dict, Optional

import hvac
from cryptography.fernet import Fernet

from .config_manager import ConfigManager
from core.exceptions import ConfigurationError


class SecureConfigManager(ConfigManager):
    """Extension of :class:`ConfigManager` that resolves ``vault:`` placeholders."""

    log = logging.getLogger(__name__)

    def __init__(
        self,
        config_path: Optional[str] = None,
        *,
        vault_addr: Optional[str] = None,
        vault_token: Optional[str] = None,
        fernet_key: Optional[str] = None,
    ) -> None:
        self.vault_addr = vault_addr or os.getenv("VAULT_ADDR")
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN")
        self.fernet_key = fernet_key or os.getenv("FERNET_KEY")

        if not self.vault_addr or not self.vault_token:
            self.log.error("Vault credentials missing")
            raise ConfigurationError(
                "VAULT_ADDR and VAULT_TOKEN must be provided for SecureConfigManager"
            )

        try:
            self.client = hvac.Client(url=self.vault_addr, token=self.vault_token)
        except Exception as exc:  # pragma: no cover - defensive
            self.log.error("Failed to initialise Vault client: %s", exc)
            raise ConfigurationError("Unable to initialise Vault client") from exc

        self.fernet = None
        if self.fernet_key:
            try:
                self.fernet = Fernet(self.fernet_key)
            except Exception as exc:  # pragma: no cover - defensive
                self.log.warning("Invalid Fernet key: %s", exc)

        super().__init__(config_path=config_path)

    # ------------------------------------------------------------------
    def reload_config(self) -> None:  # noqa: D401 - inherit docstring
        super().reload_config()
        self._resolve_vault_values(self.config)

    # ------------------------------------------------------------------
    def _read_secret(self, path: str, field: Optional[str]) -> Optional[str]:
        if not self.client:
            self.log.error("Vault client not initialised")
            raise ConfigurationError("Vault client not initialised")
        try:
            secret = self.client.secrets.kv.v2.read_secret_version(path=path)
            data: Dict[str, Any] = secret["data"]["data"]
            value = data.get(field) if field else data
            if isinstance(value, str) and self.fernet:
                try:
                    value = self.fernet.decrypt(value.encode()).decode()
                except Exception as exc:  # pragma: no cover - defensive
                    self.log.warning("Failed to decrypt %s: %s", path, exc)
            return value  # type: ignore[return-value]
        except Exception as exc:  # pragma: no cover - defensive
            self.log.error("Failed to read secret %s: %s", path, exc)
            raise ConfigurationError(f"Failed to read secret {path}") from exc

    def _resolve_vault_values(self, obj: Any) -> Any:
        if isinstance(obj, str) and obj.startswith("vault:"):
            path = obj[6:]
            secret_path, field = (path.split("#", 1) + [None])[:2]
            return self._read_secret(secret_path, field)
        if isinstance(obj, list):
            return [self._resolve_vault_values(v) for v in obj]
        if isinstance(obj, dict):
            return {k: self._resolve_vault_values(v) for k, v in obj.items()}
        if is_dataclass(obj):
            for field_name in obj.__dataclass_fields__:
                value = getattr(obj, field_name)
                setattr(obj, field_name, self._resolve_vault_values(value))
            return obj
        if hasattr(obj, "__dict__"):
            for key, value in vars(obj).items():
                setattr(obj, key, self._resolve_vault_values(value))
            return obj
        return obj


__all__ = ["SecureConfigManager"]

