#!/usr/bin/env python3
"""
Core package initialization - Fixed for streamlined architecture
"""
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


# Lazy import to avoid heavy dash dependencies during package import
def create_app(mode: str | None = None):
    """Proxy to :func:`core.app_factory.create_app` loaded lazily."""
    from .app_factory import create_app as _create_app

    return _create_app(mode)


__all__ = ["create_app"]
