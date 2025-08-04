"""Lightweight import utilities for tests and optional dependencies."""

from .resolver import safe_import, register_fallback

__all__ = ["safe_import", "register_fallback"]

