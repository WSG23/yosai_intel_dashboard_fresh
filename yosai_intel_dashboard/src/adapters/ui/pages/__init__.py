"""Page callback registry and helper for registering all callbacks."""

from typing import Iterable

from yosai_intel_dashboard.src.callbacks.controller import register_callbacks

FEATURES: Iterable[str] = ["greetings", "upload", "device_learning", "data_enhancer"]

# Import subpackages so ``from ... import greetings`` works
for name in FEATURES:
    try:  # pragma: no cover - optional pages
        globals()[name] = import_module(f"{__name__}.{name}")
    except Exception:  # pragma: no cover - optional pages
        continue

__all__ = [*FEATURES, "register_callbacks"]
