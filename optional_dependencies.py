import importlib
import logging
logger = logging.getLogger("optional_dependencies")

def import_optional(modpath: str):
    try:
        return importlib.import_module(modpath)
    except Exception as e:
        logger.error("Error importing optional dependency %r: %s", modpath, e)
        return None
