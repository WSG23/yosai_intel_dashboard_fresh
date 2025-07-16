#!/usr/bin/env python3
"""
Page registration system - Fixed to work with Dash app context
"""

import importlib
import logging
import dash_bootstrap_components as dbc
from types import ModuleType
from typing import TYPE_CHECKING, Callable, Dict, Optional, Any

if TYPE_CHECKING:
    from dash import Dash

logger = logging.getLogger(__name__)

# Mapping of page names to their module paths
PAGE_MODULES: Dict[str, str] = {
    "deep_analytics": "pages.deep_analytics",
    "file_upload": "pages.file_upload",
    "graphs": "pages.graphs",
    "export": "pages.export",
    "settings": "pages.settings",
    "device_analysis": "pages.device_analysis",
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


def register_pages(app: Optional["Dash"] = None) -> None:
    """Register all known pages with a Dash app."""
    registered_count = 0
    failed_pages = []
    
    for name in PAGE_MODULES:
        try:
            module = _load_page(name)
            if module and hasattr(module, "register_page"):
                module.register_page(app=app)
                registered_count += 1
                logger.debug(f"✅ Registered page: {name}")
            else:
                logger.debug(f"⚠️ No register_page function in {name}")
        except Exception as exc:
            failed_pages.append(name)
            logger.warning(f"❌ Failed to register page {name}: {exc}")
    
    if app is not None:
        # Check what pages were actually registered
        try:
            from dash.page_registry import page_registry
            actual_registered = list(page_registry.keys())
            logger.info(f"🔍 Dash page registry contains: {actual_registered}")
        except (ImportError, AttributeError):
            logger.debug("Could not access page registry")
    
    logger.info(f"✅ Pages registered: {registered_count}/{len(PAGE_MODULES)}")
    if failed_pages:
        logger.warning(f"❌ Failed to register: {failed_pages}")


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
        status[name] = module is not None and hasattr(module, "layout")
    return status


# Alternative manual routing system for when Dash Pages fails

def create_manual_router(app):
    """Create manual routing - now integrated with TrulyUnifiedCallbacks."""
    pass  # Routing handled by register_router_callback

def register_router_callback(manager):
    """Register routing callback with TrulyUnifiedCallbacks."""
    from dash import Input, Output, html
    
    def route_pages_unified(pathname):
        try:
            path_mapping = {
                "/": "deep_analytics",
                "/analytics": "deep_analytics",
                "/dashboard": "deep_analytics",
                "/upload": "file_upload",
                "/export": "export",
                "/settings": "settings",
                "/graphs": "graphs",
                "/device-analysis": "device_analysis",
            }
            
            page_name = path_mapping.get(pathname, "deep_analytics")
            layout_func = get_page_layout(page_name)
            
            if layout_func:
                return layout_func()
            else:
                return html.Div([
                    html.H1("Page Not Found"),
                    html.P(f"Could not load page: {page_name}"),
                    html.P(f"Path: {pathname}")
                ])
        except Exception as exc:
            logger.exception("Routing failure")
            return dbc.Alert(
                "There was a problem loading the requested page.",
                color="danger",
            )
    
    # Register with TrulyUnifiedCallbacks
    manager.unified_callback(
        Output("page-content", "children"),
        Input("url", "pathname"),
        prevent_initial_call=False
    )(route_pages_unified)


def register_all_pages(app: "Dash", manager: Optional[Any] = None) -> None:
    """Register every page module and its callbacks with *app*."""
    import pkgutil
    from pathlib import Path

    package_path = Path(__file__).parent
    modules = [m.name for m in pkgutil.iter_modules([str(package_path)]) if not m.name.startswith("_")]

    for mod_name in modules:
        try:
            module = importlib.import_module(f"{__name__}.{mod_name}")
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("Failed to import %s: %s", mod_name, exc)
            continue

        if hasattr(module, "register_page"):
            try:
                module.register_page(app=app)
                logger.debug("Registered page %s", mod_name)
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning("Failed to register page %s: %s", mod_name, exc)

        if manager and hasattr(module, "register_callbacks"):
            try:
                module.register_callbacks(manager)
                logger.debug("Registered callbacks for %s", mod_name)
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning("Failed to register callbacks for %s: %s", mod_name, exc)
