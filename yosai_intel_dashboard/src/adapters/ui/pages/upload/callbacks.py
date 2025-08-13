"""Backward compatible wrapper for upload callbacks."""
from yosai_intel_dashboard.src.callbacks.controller import (
    register_upload_callbacks as register_callbacks,
)

__all__ = ["register_callbacks"]
