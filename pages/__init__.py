#!/usr/bin/env python3
"""
Page registration system for dynamic page loading.
Replace existing pages/__init__.py entirely.
"""

import importlib
import logging
from types import ModuleType
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)

# Mapping of page names to their module paths
PAGE_MODULES: Dict[str, str] = {
    "deep_analytics": "pages.deep_analytics",
    "file_upload": "pages.file_upload",
    "graphs": "pages.graphs",
    "export": "pages.export",
    "settings": "pages.settings",
}

# Cache of loaded page modules
_loaded: Dict[str, Optional[ModuleType]] = {}


def _load_page(name: str) -> Optional[ModuleType]:
    """Import and cache the page module by name."""
    if name in _loaded:
        return _loaded[name]

    module_path = PAGE_MODULES.get(name)
    if not module_path:
        logger.warning(f"Unknown page requested: {name}")
        _loaded[name] = None
        return None

    try:
        module = importlib.import_module(module_path)
        _loaded[name] = module
        return module
    except Exception as e:
        logger.warning(f"Failed to import page {name}: {e}")
        _loaded[name] = None
        return None


def get_page_layout(page_name: str) -> Optional[Callable]:
    """Get the layout function for a given page if available."""
    module = _load_page(page_name)
    if module and hasattr(module, "layout"):
        return getattr(module, "layout")
    return None


def register_pages() -> None:
    """Register all known pages with Dash."""
    for name in PAGE_MODULES:
        module = _load_page(name)
        if module and hasattr(module, "register_page"):
            try:
                module.register_page()
            except Exception as exc:
                logger.warning(f"Failed to register page {name}: {exc}")


__all__ = ["get_page_layout", "register_pages"]
