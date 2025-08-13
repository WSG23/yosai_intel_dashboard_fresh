"""Backward compatible wrapper for device learning callbacks."""
from yosai_intel_dashboard.src.callbacks.controller import (
    register_device_learning_callbacks as register_callbacks,
)

__all__ = ["register_callbacks"]
