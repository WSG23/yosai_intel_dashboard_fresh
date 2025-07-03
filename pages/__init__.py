#!/usr/bin/env python3
"""
Simplified Pages Package
"""
import logging
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)

# Only import existing pages
_pages = {}

try:
    from . import deep_analytics
    _pages["deep_analytics"] = deep_analytics
except ImportError as e:
    logger.warning(f"Deep analytics page not available: {e}")
    _pages["deep_analytics"] = None

try:
    from . import file_upload
    _pages["file_upload"] = file_upload
except ImportError as e:
    logger.warning(f"File upload page not available: {e}")
    _pages["file_upload"] = None

try:
    from . import dashboard
    _pages["dashboard"] = dashboard
except ImportError as e:
    logger.warning(f"Dashboard page not available: {e}")
    _pages["dashboard"] = None

try:
    from . import graphs
    _pages["graphs"] = graphs
except ImportError as e:
    logger.warning(f"Graphs page not available: {e}")
    _pages["graphs"] = None

try:
    from . import settings
    _pages["settings"] = settings
except ImportError as e:
    logger.warning(f"Settings page not available: {e}")
    _pages["settings"] = None

def get_page_layout(page_name: str) -> Optional[Callable]:
    """Get page layout function safely"""
    page_module = _pages.get(page_name)
    if page_module and hasattr(page_module, 'layout'):
        return page_module.layout
    return None

__all__ = ['get_page_layout']
