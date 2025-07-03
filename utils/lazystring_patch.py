#!/usr/bin/env python3
"""
Emergency LazyString monkey patch for JSON serialization
Apply this patch as early as possible in your application startup
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Store original json.dumps
_original_json_dumps = json.dumps


def lazystring_safe_json_dumps(obj: Any, **kwargs) -> str:
    """Monkey-patched json.dumps that handles LazyString objects"""

    def safe_default(o):
        # Handle LazyString objects
        if hasattr(o, "__class__") and "LazyString" in str(o.__class__):
            return str(o)

        # Handle Babel lazy objects
        if hasattr(o, "_func") and hasattr(o, "_args"):
            try:
                return str(o)
            except Exception:
                return f"LazyString: {repr(o)}"

        # Handle functions
        if callable(o):
            return f"<function {getattr(o, '__name__', 'anonymous')}>"

        # Fallback to string representation
        return str(o)

    # If no default serializer provided, use our safe one
    if "default" not in kwargs:
        kwargs["default"] = safe_default

    try:
        return _original_json_dumps(obj, **kwargs)
    except Exception as e:
        logger.warning(f"JSON serialization failed, using safe fallback: {e}")
        # Ultimate fallback
        return _original_json_dumps(
            {
                "error": "Serialization failed",
                "message": str(e),
                "safe_repr": str(obj)[:200],
            }
        )


def apply_lazystring_patch():
    """Apply the LazyString monkey patch to json.dumps"""
    json.dumps = lazystring_safe_json_dumps
    logger.info("✅ LazyString monkey patch applied to json.dumps")


def remove_lazystring_patch():
    """Remove the LazyString monkey patch"""
    json.dumps = _original_json_dumps
    logger.info("LazyString monkey patch removed")


# Auto-apply the patch when imported
apply_lazystring_patch()
