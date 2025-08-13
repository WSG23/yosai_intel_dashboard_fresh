from .analytics_utils import ensure_model_downloaded, preload_active_models
from .config_utils import common_init, create_config_methods

try:  # pragma: no cover - optional dependency
    from .model_registry import ModelRegistry  # type: ignore
except Exception:  # pragma: no cover - fallback when unavailable
    ModelRegistry = None  # type: ignore

__all__ = [
    "ModelRegistry",
    "create_config_methods",
    "common_init",
    "ensure_model_downloaded",
    "preload_active_models",
]
