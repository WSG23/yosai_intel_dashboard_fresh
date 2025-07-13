#!/usr/bin/env python3
"""
Page registration system - Fixed to work with Dash app context
"""

import importlib
import logging
from types import ModuleType
from typing import TYPE_CHECKING, Callable, Dict, Optional

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
    """Register all known pages with manual routing only."""
    # Skip Dash Pages registration entirely - use manual routing only
    logger.info("✅ Skipping Dash Pages - using manual routing only")
    registered_count = len(PAGE_MODULES)
    logger.info(f"✅ Pages available for manual routing: {registered_count}/{len(PAGE_MODULES)}")

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
def create_manual_router(app: "Dash") -> None:
    """Create manual routing when Dash Pages fails."""
    from dash import Input, Output, dcc, html
    
    # Create simple router callback
    @app.callback(
        Output("page-content", "children"),
        Input("url", "pathname"),
        prevent_initial_call=False
    )
    def route_pages(pathname):
        """Manual page routing."""
        try:
            # Map paths to page names
            path_mapping = {
                "/": "deep_analytics",
                "/analytics": "deep_analytics", 
                "/dashboard": "deep_analytics",
                "/upload": "file_upload",
                "/export": "export",
                "/settings": "settings",
                "/graphs": "graphs",
            }
            
            page_name = path_mapping.get(pathname, "deep_analytics")
            layout_func = get_page_layout(page_name)
            
            if layout_func:
                return layout_func()
            else:
                return html.Div([
                    html.H1("Page Not Found"),
                    html.P(f"Could not load page: {page_name}"),
                    html.P(f"Requested path: {pathname}"),
                ])
                
        except Exception as e:
            logger.error(f"Router error for {pathname}: {e}")
            return html.Div([
                html.H1("Error"),
                html.P(f"Error loading page: {str(e)}"),
            ])
    
    logger.info("✅ Manual router created")


__all__ = [
    "register_pages", 
    "get_page_layout", 
    "clear_page_cache", 
    "get_available_pages",
    "create_manual_router",
    "PAGE_MODULES"
]
