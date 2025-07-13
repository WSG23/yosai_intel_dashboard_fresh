"""Load configuration files with YAML ``!include`` support."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

from pathlib import Path

from .environment import select_config_file
from .protocols import ConfigLoaderProtocol
from .base_loader import BaseConfigLoader


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
        return validate_uploads_config(data)


__all__ = ["ConfigLoader", "ConfigLoaderProtocol", "validate_uploads_config"]
