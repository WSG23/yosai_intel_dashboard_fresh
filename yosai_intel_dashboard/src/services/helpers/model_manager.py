from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, TYPE_CHECKING

import requests

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
        dest = dest / name / record.version
        dest.mkdir(parents=True, exist_ok=True)
        local_path = dest / Path(record.storage_uri).name

        local_version = self._registry.get_version_metadata(name)
        if local_version == record.version and local_path.exists():
            return str(local_path)

        try:
            self._registry.download_artifact(record.storage_uri, str(local_path))
            self._registry.store_version_metadata(name, record.version)
            return str(local_path)
        except (
            OSError,
            RuntimeError,
            requests.RequestException,
            ValueError,
        ) as exc:  # pragma: no cover - best effort
            logger.error(
                "Failed to download model %s (%s): %s", name, type(exc).__name__, exc
            )
            return None


__all__ = ["ModelManager"]
