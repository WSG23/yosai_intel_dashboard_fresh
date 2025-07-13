#!/usr/bin/env python3
"""
Page registration system - simplified to prevent routing conflicts
"""

# Expected page modules bundled with the application. Each listed module must
# provide at least a ``layout`` function and may optionally expose a
# ``register_page`` hook for Dash integration.
#
# - ``deep_analytics``
# - ``file_upload``
# - ``graphs``
# - ``export``
# - ``settings``

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
        logger.debug(f"✅ Loaded page module: {name}")
        return module
    except Exception:
        logger.exception(f"❌ Failed to import page {name}")
        _loaded[name] = None
        return None


def get_page_layout(page_name: str) -> Optional[Callable]:
    """Get the layout function for a given page if available."""
    module = _load_page(page_name)
    if module and hasattr(module, "layout"):
        return getattr(module, "layout")
    return None


def register_pages() -> None:
    """Register all known pages with Dash - simplified version."""
    registered_count = 0
    
    for name in PAGE_MODULES:
        try:
            module = _load_page(name)
            if module and hasattr(module, "register_page"):
                module.register_page()
                registered_count += 1
                logger.debug(f"✅ Registered page: {name}")
            else:
                logger.debug(f"⚠️ No register_page function in {name}")
        except Exception as exc:
            logger.warning(f"❌ Failed to register page {name}: {exc}")
    
    logger.info(f"✅ Pages registered: {registered_count}/{len(PAGE_MODULES)}")


def clear_page_cache() -> None:
    """Clear the page module cache."""
    global _loaded
    _loaded.clear()
    logger.info("🔄 Page cache cleared")


def get_available_pages() -> Dict[str, bool]:
    """Get status of all available pages."""
    status = {}
    for name in PAGE_MODULES:
        module = _load_page(name)
        status[name] = module is not None
    return status


__all__ = ["get_page_layout", "register_pages", "clear_page_cache", "get_available_pages"]

def __getattr__(name: str):
    if name.startswith(("create_", "get_")):
        def _stub(*args, **kwargs):
            return None
        return _stub
    raise AttributeError(f"module {__name__} has no attribute {name}")
