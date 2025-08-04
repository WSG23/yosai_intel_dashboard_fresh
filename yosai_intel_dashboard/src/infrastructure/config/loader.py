"""Aggregate configuration from files and environment variables.

This module provides :class:`ConfigurationLoader` which loads configuration
data from the standard configuration files and overlays any environment based
settings.  It exposes a :meth:`get_service_config` helper that returns a
``ServiceSettings`` dataclass used by a number of microservices.  The loader
also inherits :class:`ConfigurationMixin` so that it satisfies the
``ConfigurationProtocol`` used throughout the codebase.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .base_loader import BaseConfigLoader
from .config_loader import ServiceSettings
from .configuration_mixin import ConfigurationMixin
from .environment import select_config_file


class ConfigurationLoader(ConfigurationMixin, BaseConfigLoader):
    """Loader that merges file based configuration with environment settings."""

    log = logging.getLogger(__name__)

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config_path = config_path
        self._config = self._load_config()
        # Expose top level keys as attributes so ConfigurationMixin can access
        # nested sections using attribute lookups.
        for key, value in self._config.items():
            setattr(self, key, value)

    # ------------------------------------------------------------------
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration data from file or ``YOSAI_CONFIG_JSON``."""

        path = select_config_file(config_path or self.config_path)
        data: Dict[str, Any] = {}
        if path and path.exists():
            try:
                data = self.load_file(path)
            except Exception as exc:  # pragma: no cover - defensive
                self.log.warning("Failed to load %s: %s", path, exc)

        env_json = os.getenv("YOSAI_CONFIG_JSON")
        if env_json:
            try:
                env_data = json.loads(env_json)
                data.update(env_data)
            except Exception as exc:  # pragma: no cover - defensive
                self.log.warning("Failed to parse YOSAI_CONFIG_JSON: %s", exc)

        return data

    # ------------------------------------------------------------------
    def get_service_config(self) -> ServiceSettings:
        """Return ``ServiceSettings`` populated from config and environment."""

        cfg = self._config.get("service", {})
        return ServiceSettings(
            redis_url=os.getenv("REDIS_URL", cfg.get("redis_url", ServiceSettings.redis_url)),
            cache_ttl=int(
                os.getenv("CACHE_TTL", cfg.get("cache_ttl", ServiceSettings.cache_ttl))
            ),
            model_dir=Path(
                os.getenv("MODEL_DIR", cfg.get("model_dir", ServiceSettings.model_dir))
            ),
            registry_db=os.getenv(
                "MODEL_REGISTRY_DB", cfg.get("registry_db", ServiceSettings.registry_db)
            ),
            registry_bucket=os.getenv(
                "MODEL_REGISTRY_BUCKET",
                cfg.get("registry_bucket", ServiceSettings.registry_bucket),
            ),
            mlflow_uri=os.getenv("MLFLOW_URI", cfg.get("mlflow_uri")),
        )


__all__ = ["ConfigurationLoader", "ServiceSettings"]

