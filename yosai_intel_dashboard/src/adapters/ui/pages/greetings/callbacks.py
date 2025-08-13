"""Backward compatible wrapper for greetings callbacks."""
from yosai_intel_dashboard.src.callbacks.controller import (
    register_greetings_callbacks as register_callbacks,
)

__all__ = ["register_callbacks"]
