from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from yosai_intel_dashboard.models.ml import ModelRegistry


def preload_active_models(service: Any) -> None:
    """Load active models into memory from the registry.

    Parameters
    ----------
    service:
        Analytics service instance with ``model_registry``, ``model_dir`` and
        ``models`` attributes.
    """
    service.models = {}
    registry: ModelRegistry = service.model_registry
    try:
        records = registry.list_models()
    except Exception:  # pragma: no cover - registry unavailable
        return
    names = {r.name for r in records}
    for name in names:
        record = registry.get_model(name, active_only=True)
        if record is None:
            continue
        local_dir = Path(service.model_dir) / name / record.version
        local_dir.mkdir(parents=True, exist_ok=True)
        filename = os.path.basename(record.storage_uri)
        local_path = local_dir / filename
        if not local_path.exists():
            try:
                registry.download_artifact(record.storage_uri, str(local_path))
            except Exception:  # pragma: no cover - best effort
                continue
        try:
            import joblib

            model_obj = joblib.load(local_path)
            service.models[name] = model_obj
        except Exception:  # pragma: no cover - invalid model
            continue
