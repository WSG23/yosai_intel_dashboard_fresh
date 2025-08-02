"""Config manager that fetches secrets from HashiCorp Vault."""

from __future__ import annotations

import logging
import os
from dataclasses import is_dataclass
from typing import Any, Dict, Optional

from botocore.exceptions import ClientError
from optional_dependencies import import_optional

boto3 = import_optional("boto3")
hvac = import_optional("hvac")
fernet_mod = import_optional("cryptography.fernet")
Fernet = getattr(fernet_mod, "Fernet", None)
from pydantic import BaseModel

from yosai_intel_dashboard.src.core.exceptions import ConfigurationError

from .config_manager import ConfigManager


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
        aws_region: Optional[str] = None,
    ) -> None:
        self.vault_addr = vault_addr or os.getenv("VAULT_ADDR")
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN")
        self.fernet_key = fernet_key or os.getenv("FERNET_KEY")
        self.aws_region = aws_region or os.getenv("AWS_REGION")

        self.client = None
        if hvac and self.vault_addr and self.vault_token:
            try:
                self.client = hvac.Client(url=self.vault_addr, token=self.vault_token)
            except Exception as exc:  # pragma: no cover - defensive
                self.log.error("Failed to initialise Vault client: %s", exc)
                raise ConfigurationError("Unable to initialise Vault client") from exc

        self.aws_client = None
        if self.aws_region and boto3:
            try:
                self.aws_client = boto3.client(
                    "secretsmanager", region_name=self.aws_region
                )
            except Exception as exc:  # pragma: no cover - defensive
                self.log.error("Failed to initialise AWS client: %s", exc)
                raise ConfigurationError("Unable to initialise AWS client") from exc

        self.fernet = None
        if self.fernet_key and Fernet:
            try:
                self.fernet = Fernet(self.fernet_key)
            except Exception as exc:  # pragma: no cover - defensive
                self.log.warning("Invalid Fernet key: %s", exc)

        super().__init__(config_path=config_path)

    # ------------------------------------------------------------------
    def reload_config(self) -> None:  # noqa: D401 - inherit docstring
        super().reload_config()
        self._resolve_secret_values(self.config)

    # ------------------------------------------------------------------
    def _read_vault_secret(self, path: str, field: Optional[str]) -> Optional[str]:
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

    def _read_aws_secret(self, name: str) -> Optional[str]:
        if not self.aws_client:
            self.log.error("AWS client not initialised")
            raise ConfigurationError("AWS client not initialised")
        try:
            secret = self.aws_client.get_secret_value(SecretId=name)
            if "SecretString" in secret:
                return secret["SecretString"]
            if "SecretBinary" in secret:
                return secret["SecretBinary"].decode()
            return None
        except self.aws_client.exceptions.ResourceNotFoundException:  # type: ignore[attr-defined]
            self.log.error("Secret %s not found", name)
            raise ConfigurationError(f"AWS secret {name} not found")
        except ClientError as exc:  # pragma: no cover - defensive
            self.log.error("Failed to read AWS secret %s: %s", name, exc)
            raise ConfigurationError(f"Failed to read AWS secret {name}") from exc

    def _resolve_secret_values(self, obj: Any) -> Any:
        if isinstance(obj, str):
            if obj.startswith("vault:"):
                path = obj[6:]
                secret_path, field = (path.split("#", 1) + [None])[:2]
                return self._read_vault_secret(secret_path, field)
            if obj.startswith("aws-secrets:"):
                name = obj[len("aws-secrets:") :]
                return self._read_aws_secret(name)
            return obj
        if isinstance(obj, list):
            return [self._resolve_secret_values(v) for v in obj]
        if isinstance(obj, dict):
            return {k: self._resolve_secret_values(v) for k, v in obj.items()}
        if is_dataclass(obj):
            for field_name in obj.__dataclass_fields__:
                value = getattr(obj, field_name)
                setattr(obj, field_name, self._resolve_secret_values(value))
            return obj
        if isinstance(obj, BaseModel):
            for name, value in obj.model_dump().items():  # type: ignore[arg-type]
                resolved = self._resolve_secret_values(value)
                object.__setattr__(obj, name, resolved)
            return obj
        if hasattr(obj, "__dict__"):
            for key, value in vars(obj).items():
                setattr(obj, key, self._resolve_secret_values(value))
            return obj
        return obj


__all__ = ["SecureConfigManager"]
