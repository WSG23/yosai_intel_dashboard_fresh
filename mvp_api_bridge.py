from __future__ import annotations
import importlib, os, traceback
from typing import Any
from fastapi import FastAPI

DEFAULT_SPEC = "yosai_intel_dashboard.src.adapters.api.adapter:create_api_app"

def _load_obj(spec: str) -> Any | None:
    mod, _, attr = spec.partition(":")
    m = importlib.import_module(mod)
    obj = getattr(m, attr) if attr else getattr(m, "app", None)
    return obj() if callable(obj) else obj

def try_mount_real_api(app: FastAPI) -> str:
    spec = os.getenv("YOSAI_REALAPI_SPEC", DEFAULT_SPEC) or DEFAULT_SPEC
    debug = os.getenv("BRIDGE_DEBUG", "0") == "1"
    try:
        real = _load_obj(spec)
        if real is None:
            if debug: print(f"[bridge] loaded None from {spec}")
            return ""
        app.mount("/realapi", real)
        if debug: print(f"[bridge] mounted {spec} at /realapi")
        return spec
    except Exception as e:
        if debug:
            print(f"[bridge] failed to mount {spec}: {e}")
            traceback.print_exc()
        return ""
