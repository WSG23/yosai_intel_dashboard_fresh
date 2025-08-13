"""Compatibility wrapper for greeting callbacks."""

from yosai_intel_dashboard.src.callbacks.controller import (
    register_greeting_callbacks as register_callbacks,
)

__all__ = ["register_callbacks"]
