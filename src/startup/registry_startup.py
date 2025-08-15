"""Initialize the optional service registry after configuration loads."""
from __future__ import annotations

from yosai_intel_dashboard.src.core.registry import register_builtin_services


def register_optional_services() -> None:
    """Register built-in optional services."""

    register_builtin_services()

__all__ = ["register_optional_services"]
