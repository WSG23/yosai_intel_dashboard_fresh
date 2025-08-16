from __future__ import annotations
import importlib, logging, os
from typing import Any
from fastapi import FastAPI

DEFAULT_SPEC = "yosai_intel_dashboard.src.adapters.api.adapter:create_api_app"

# module status dictionary tracking mount state and errors
_status: dict[str, Any] = {"mounted": False, "spec": None, "error": None}

# logger for bridge operations
logger = logging.getLogger("bridge")

def _load_obj(spec: str) -> Any | None:
    mod, _, attr = spec.partition(":")
    m = importlib.import_module(mod)
    obj = getattr(m, attr) if attr else getattr(m, "app", None)
    return obj() if callable(obj) else obj

def try_mount_real_api(app: FastAPI) -> str:
    """Attempt to mount the real API and update status/logs."""
    spec = os.getenv("YOSAI_REALAPI_SPEC", DEFAULT_SPEC) or DEFAULT_SPEC
    _status.update(spec=spec, mounted=False, error=None)
    try:
        real = _load_obj(spec)
        if real is None:
            msg = f"loaded None from {spec}"
            _status.update(error=msg)
            logger.error("%s", msg)
            return ""
        app.mount("/realapi", real)
        _status.update(mounted=True)
        logger.info("mounted %s at /realapi", spec)
        return spec
    except Exception as e:
        _status.update(error=str(e))
        logger.exception("failed to mount %s", spec)
        return ""
