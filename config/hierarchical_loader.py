"""Hierarchical configuration loader using multiple layers."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import BaseModel, ConfigDict

from .base_loader import BaseConfigLoader
from .environment import get_environment
from .protocols import ConfigLoaderProtocol


class AppSettings(BaseModel):
    """Minimal application settings with defaults."""

    model_config = ConfigDict(extra="allow")

    title: str = "Y\u014dsai Intel Dashboard"
    debug: bool = True
    host: str = "127.0.0.1"
    port: int = 8050
    secret_key: str = ""
    environment: str = "development"


class DatabaseSettings(BaseModel):
    """Database defaults."""

    model_config = ConfigDict(extra="allow")

    type: str = "sqlite"
    host: str = "localhost"
    port: int = 5432
    name: str = "yosai.db"
    user: str = "user"
    password: str = ""
    url: str = ""


class SecuritySettings(BaseModel):
    """Security defaults."""

    model_config = ConfigDict(extra="allow")

    secret_key: str = ""
    max_upload_mb: int = 50
    allowed_file_types: list[str] = [".csv", ".json", ".xlsx"]


class ConfigDefaults(BaseModel):
    """Top level configuration defaults."""

    model_config = ConfigDict(extra="allow")

    app: AppSettings = AppSettings()
    database: DatabaseSettings = DatabaseSettings()
    security: SecuritySettings = SecuritySettings()
    plugin_settings: Dict[str, Dict[str, Any]] = {}
    environment: str = "development"


class HierarchicalLoader(BaseConfigLoader, ConfigLoaderProtocol):
    """Load configuration from layered sources."""

    log = logging.getLogger(__name__)

    def __init__(self, environment: str | None = None) -> None:
        self.environment = environment or get_environment()

    # ------------------------------------------------------------------
    def _read_yaml(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        try:
            with path.open("r", encoding="utf-8") as fh:
                return yaml.safe_load(fh) or {}
        except Exception as exc:  # pragma: no cover - defensive
            self.log.warning("Failed to load %s: %s", path, exc)
            return {}

    def _read_dir(self, path: Path) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        if not path.is_dir():
            return data
        for file in sorted(path.rglob("*.yaml")):
            data.update(self._read_yaml(file))
        return data

    def _convert(self, value: str) -> Any:
        low = value.lower()
        if low in {"true", "1", "yes"}:
            return True
        if low in {"false", "0", "no"}:
            return False
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        try:
            return json.loads(value)
        except Exception:
            return value

    def _load_env(self) -> Dict[str, Any]:
        overrides: Dict[str, Dict[str, Any]] = {}
        for name, value in os.environ.items():
            if not name.startswith("YOSAI_"):
                continue
            parts = name[6:].lower().split("_", 1)
            if len(parts) != 2:
                continue
            section, field = parts
            overrides.setdefault(section, {})[field] = self._convert(value)
        return overrides

    def _load_feature_flags(self) -> Dict[str, Any]:
        path = Path("k8s/config/feature-flags.yaml")
        if path.exists():
            data = self._read_yaml(path)
            flags = data.get("data", {}) if isinstance(data, dict) else {}
            return {"features": {k: self._convert(v) for k, v in flags.items()}}
        env_json = os.getenv("FEATURE_FLAGS")
        if env_json:
            try:
                return {"features": json.loads(env_json)}
            except Exception:  # pragma: no cover - defensive
                self.log.warning("Failed to parse FEATURE_FLAGS")
        return {}

    # ------------------------------------------------------------------
    def load(self, config_path: str | None = None) -> Dict[str, Any]:
        """Load configuration from defaults, files and environment."""
        cfg_dict = ConfigDefaults().model_dump()

        env_file = (
            Path(config_path)
            if config_path
            else Path("config/environments") / f"{self.environment}.yaml"
        )
        cfg_dict.update(self._read_yaml(env_file))

        for folder in ("k8s", "helm"):
            cfg_dict.update(self._read_dir(Path(folder)))

        self._deep_update(cfg_dict, self._load_env())
        self._deep_update(cfg_dict, self._load_feature_flags())

        return cfg_dict

    # ------------------------------------------------------------------
    def _deep_update(self, base: Dict[str, Any], updates: Dict[str, Any]) -> None:
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value


__all__ = ["HierarchicalLoader"]
