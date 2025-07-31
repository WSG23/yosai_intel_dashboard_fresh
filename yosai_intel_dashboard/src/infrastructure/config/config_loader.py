"""Load configuration files with YAML ``!include`` support."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from .base_loader import BaseConfigLoader
from .environment import select_config_file
from .protocols import ConfigLoaderProtocol


@dataclass
class ServiceSettings:
    """Settings specific to microservices."""

    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 300
    model_dir: Path = Path("model_store")
    registry_db: str = "sqlite:///model_registry.db"
    registry_bucket: str = "local-models"
    mlflow_uri: Optional[str] = None


def load_service_config() -> ServiceSettings:
    """Return service settings from environment with defaults."""

    return ServiceSettings(
        redis_url=os.getenv("REDIS_URL", ServiceSettings.redis_url),
        cache_ttl=int(os.getenv("CACHE_TTL", str(ServiceSettings.cache_ttl))),
        model_dir=Path(os.getenv("MODEL_DIR", str(ServiceSettings.model_dir))),
        registry_db=os.getenv("MODEL_REGISTRY_DB", ServiceSettings.registry_db),
        registry_bucket=os.getenv(
            "MODEL_REGISTRY_BUCKET", ServiceSettings.registry_bucket
        ),
        mlflow_uri=os.getenv("MLFLOW_URI"),
    )


def validate_uploads_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate uploads configuration with defaults."""
    defaults = {
        "max_file_size": 104857600,
        "allowed_extensions": [".csv", ".xlsx", ".json"],
        "scan_for_malware": True,
    }

    if "uploads" not in config:
        config["uploads"] = defaults
    else:
        for key, default_value in defaults.items():
            if key not in config["uploads"]:
                config["uploads"][key] = default_value

    return config


class ConfigLoader(BaseConfigLoader, ConfigLoaderProtocol):
    """Load configuration from YAML/JSON files or environment.

    The loader understands a custom ``!include`` YAML tag which allows other
    YAML files to be recursively included relative to the current file.
    """

    log = logging.getLogger(__name__)

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config_path = config_path

    def load(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        path = select_config_file(config_path or self.config_path)
        data: Dict[str, Any] = {}
        if path and path.exists():
            try:
                data = self.load_file(path)
            except Exception as exc:  # pragma: no cover - defensive
                self.log.warning("Failed to load %s: %s", path, exc)

        env_json = os.getenv("YOSAI_CONFIG_JSON")
        if not data and env_json:
            try:
                data = json.loads(env_json)
            except Exception as exc:  # pragma: no cover - defensive
                self.log.warning("Failed to parse YOSAI_CONFIG_JSON: %s", exc)

        data = self._sanitize(data)

        if "database" in data and not data["database"].get("password"):
            if env_pwd := os.getenv("DB_PASSWORD"):
                data.setdefault("database", {})["password"] = env_pwd

        return validate_uploads_config(data)


__all__ = [
    "ConfigLoader",
    "ConfigLoaderProtocol",
    "validate_uploads_config",
    "ServiceSettings",
    "load_service_config",
]
