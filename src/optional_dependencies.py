import importlib
import logging
import types
import sys

logger = logging.getLogger("optional_dependencies")

_FALLBACKS: dict[str, types.ModuleType] = {}


def register_fallback(name: str, module: types.ModuleType) -> None:
    """Register a lightweight fallback for an optional dependency."""
    try:
        importlib.import_module(name)
    except Exception:
        _FALLBACKS[name] = module


def import_optional(modpath: str):
    try:
        return importlib.import_module(modpath)
    except Exception as e:
        logger.error("Error importing optional dependency %r: %s", modpath, e)
        return _FALLBACKS.get(modpath)
