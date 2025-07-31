"""Handle LazyString objects for JSON serialization."""

import logging
from typing import Any

from core.serialization import SafeJSONSerializer

logger = logging.getLogger(__name__)

_serializer = SafeJSONSerializer()


def sanitize_lazystring_recursive(obj: Any) -> Any:
    """Recursively convert LazyString objects to regular strings for JSON serialization"""
    try:
        return _serializer.serialize(obj)
    except Exception as e:
        logger.warning(f"Error sanitizing object {type(obj)}: {e}")
        return str(obj) if obj is not None else None
