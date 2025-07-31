#!/usr/bin/env python3
"""
Comprehensive LazyString handling utilities
Fixes all Flask-Babel LazyString JSON serialization issues
"""

import json
import logging
from typing import Any, Union

logger = logging.getLogger(__name__)

# Safe import for Flask-Babel
try:
    from flask_babel import LazyString

    BABEL_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    LazyString = None  # type: ignore
    BABEL_AVAILABLE = False


def is_lazy_string(obj: Any) -> bool:
    """Check if object is any type of LazyString"""
    if BABEL_AVAILABLE and isinstance(obj, LazyString):
        return True

    # Check by class name for different Babel versions
    class_name = str(obj.__class__)
    if "LazyString" in class_name or "lazy_string" in class_name.lower():
        return True

    # Check for lazy evaluation pattern
    if hasattr(obj, "_func") and hasattr(obj, "_args"):
        return True

    return False


def force_string_conversion(obj: Any) -> str:
    """Force conversion of any lazy string object to regular string"""
    if is_lazy_string(obj):
        try:
            return str(obj)
        except Exception as e:  # pragma: no cover - extreme edge case
            logger.warning(f"Failed to convert LazyString to string: {e}")
            return f"<LazyString conversion failed: {repr(obj)}>"

    return str(obj)


def sanitize_json_data(data: Any) -> Any:
    """Recursively sanitize data to remove all LazyString objects"""
    if is_lazy_string(data):
        return force_string_conversion(data)

    if isinstance(data, dict):
        return {key: sanitize_json_data(value) for key, value in data.items()}

    if isinstance(data, (list, tuple)):
        return type(data)(sanitize_json_data(item) for item in data)

    # Test if object is JSON serializable
    try:
        json.dumps(data)
        return data
    except (TypeError, ValueError):
        # If not serializable and has LazyString attributes, sanitize them
        if hasattr(data, "__dict__"):
            sanitized_dict = {}
            for key, value in data.__dict__.items():
                if is_lazy_string(value):
                    sanitized_dict[key] = force_string_conversion(value)
                else:
                    sanitized_dict[key] = sanitize_json_data(value)

            # Return sanitized representation
            return {"type": data.__class__.__name__, "attributes": sanitized_dict}

        # Fallback to string representation
        return str(data)


def test_json_serialization(data: Any) -> Union[str, None]:
    """Test if data can be JSON serialized, return error message if not"""
    try:
        json.dumps(data)
        return None  # Success
    except Exception as e:
        return str(e)


# Export for easy importing
__all__ = [
    "is_lazy_string",
    "force_string_conversion",
    "sanitize_json_data",
    "test_json_serialization",
]
