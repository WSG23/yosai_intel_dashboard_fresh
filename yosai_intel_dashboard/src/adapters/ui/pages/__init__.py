"""Page callback registry and helper for registering all callbacks."""

from importlib import import_module
from typing import Iterable

FEATURES: Iterable[str] = ["greetings", "upload", "device_learning", "data_enhancer"]


def register_callbacks(app, container) -> None:
    """Import each page package and register its callbacks."""
    for name in FEATURES:
        try:
            module = import_module(f"{__name__}.{name}")
        except Exception:  # pragma: no cover - optional pages
            continue

        if hasattr(module, "register_callbacks"):
            module.register_callbacks(app, container)


__all__ = [*FEATURES, "register_callbacks"]
