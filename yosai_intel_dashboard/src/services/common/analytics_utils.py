from __future__ import annotations

"""Utilities shared by analytics services."""

from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from yosai_intel_dashboard.models.ml import ModelRegistry


def ensure_model_downloaded(
    registry: "ModelRegistry", name: str, model_dir: Path
) -> Path | None:
    """Ensure the active model ``name`` exists locally.

    Parameters
    ----------
    registry:
        The :class:`ModelRegistry` instance to query.
    name:
        Name of the model to download.
    model_dir:
        Base directory where models should be stored.

    Returns
    -------
    Path | None
        Path to the downloaded model file or ``None`` if unavailable.
    """
    record = registry.get_model(name, active_only=True)
    if record is None:
        return None
    dest = model_dir / name / record.version
    dest.mkdir(parents=True, exist_ok=True)
    local_path = dest / Path(record.storage_uri).name
    if not local_path.exists():
        try:
            registry.download_artifact(record.storage_uri, local_path)
        except Exception:  # pragma: no cover - best effort
            return None
    return local_path


def preload_active_models(service: Any) -> None:
    """Load all active models from ``service.model_registry`` into memory."""
    service.models = {}
    registry: "ModelRegistry" = service.model_registry
    try:
        records = registry.list_models()
    except Exception:  # pragma: no cover - registry unavailable
        return
    names = {r.name for r in records}
    for name in names:
        path = ensure_model_downloaded(registry, name, service.model_dir)
        if path is None:
            continue
        try:
            import joblib

            service.models[name] = joblib.load(path)
        except Exception:  # pragma: no cover - invalid model
            continue


__all__ = ["ensure_model_downloaded", "preload_active_models"]
