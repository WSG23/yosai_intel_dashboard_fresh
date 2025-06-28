"""Handle LazyString objects for JSON serialization"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

def sanitize_lazystring_recursive(obj: Any) -> Any:
    """Recursively convert LazyString objects to regular strings for JSON serialization"""
    try:
        if hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
            if isinstance(obj, dict):
                return {k: sanitize_lazystring_recursive(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitize_lazystring_recursive(item) for item in obj]
            elif isinstance(obj, tuple):
                return tuple(sanitize_lazystring_recursive(item) for item in obj)
        
        # Handle LazyString objects (from Flask-Babel)
        if hasattr(obj, '__html__') or str(type(obj)).find('LazyString') != -1:
            return str(obj)
        
        # Handle Dash components
        if hasattr(obj, 'to_plotly_json'):
            json_obj = obj.to_plotly_json()
            return sanitize_lazystring_recursive(json_obj)
        
        # Handle objects with children attribute
        if hasattr(obj, 'children'):
            obj.children = sanitize_lazystring_recursive(obj.children)
        
        return obj
        
    except Exception as e:
        logger.warning(f"Error sanitizing object {type(obj)}: {e}")
        return str(obj) if obj is not None else None
