"""Page callback registry and helper for registering all callbacks."""

from typing import Iterable

from yosai_intel_dashboard.src.callbacks.controller import register_callbacks

FEATURES: Iterable[str] = ["greetings", "upload", "device_learning", "data_enhancer"]

__all__ = [*FEATURES, "register_callbacks"]
