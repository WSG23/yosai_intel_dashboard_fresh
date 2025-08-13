from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, TYPE_CHECKING

import requests

from yosai_intel_dashboard.src.services.common.analytics_utils import (
    ensure_model_downloaded,
)

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from yosai_intel_dashboard.models.ml import ModelRegistry


logger = logging.getLogger(__name__)


class ModelManager:
    """Handle interactions with the :class:`ModelRegistry`."""

    def __init__(self, registry: 'ModelRegistry' | None, config: Any | None) -> None:
        self._registry = registry
        self._config = config

    def load_model(self, name: str, *, destination_dir: str | None = None) -> str | None:
        """Download the active model ``name`` to ``destination_dir`` if needed."""
        if self._registry is None:
            return None
        record = self._registry.get_model(name, active_only=True)
        if record is None:
            return None

        models_path = getattr(self._config, "analytics", None)
        models_path = getattr(models_path, "ml_models_path", "models/ml")
        dest = Path(destination_dir or str(models_path))
        dest_path = dest / name / record.version / Path(record.storage_uri).name

        local_version = self._registry.get_version_metadata(name)
        if local_version == record.version and dest_path.exists():
            return str(dest_path)

        path = ensure_model_downloaded(self._registry, name, dest)
        if path is None:
            return None
        try:
            self._registry.store_version_metadata(name, record.version)
        except Exception:  # pragma: no cover - best effort
            logger.error("Failed to store version metadata for %s", name)
        return str(path)


__all__ = ["ModelManager"]
