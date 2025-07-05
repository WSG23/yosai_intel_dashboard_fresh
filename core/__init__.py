#!/usr/bin/env python3
"""
Core package initialization - Fixed for streamlined architecture
"""
import logging
from .dash_profile import profile_callback

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


# Lazy import to avoid heavy dash dependencies during package import
def create_app(mode: str | None = None):
    """Proxy to :func:`core.app_factory.create_app` loaded lazily."""
    from .app_factory import create_app as _create_app

    return _create_app(mode)


from typing import TYPE_CHECKING

from .unicode_processor import sanitize_unicode_input
from .unicode import (
    UnicodeTextProcessor,
    UnicodeSQLProcessor,
    UnicodeSecurityProcessor,
)
from .performance_file_processor import PerformanceFileProcessor

if TYPE_CHECKING:  # pragma: no cover - avoid circular import at runtime
    from .truly_unified_callbacks import TrulyUnifiedCallbacks


def __getattr__(name: str):
    """Lazily import heavy modules on demand."""
    if name == "TrulyUnifiedCallbacks":
        from .truly_unified_callbacks import TrulyUnifiedCallbacks as _tuc

        globals()[name] = _tuc
        return _tuc
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    "create_app",
    "profile_callback",
    "sanitize_unicode_input",
    "TrulyUnifiedCallbacks",
    "UnicodeTextProcessor",
    "UnicodeSQLProcessor",
    "UnicodeSecurityProcessor",
    "PerformanceFileProcessor",
]
