from __future__ import annotations

import importlib
import os
from typing import Any

from fastapi import FastAPI


DEFAULT_SPEC = "yosai_intel_dashboard.src.adapters.api.adapter:create_api_app"


def try_mount_real_api(app: FastAPI) -> str:
    """Attempt to mount the real API under `/realapi`.

    Returns the spec string if mounted, otherwise an empty string. Any
    exceptions during import or mounting are swallowed to avoid impacting the
    MVP server.
    """

    spec = os.getenv("YOSAI_REALAPI_SPEC", DEFAULT_SPEC)
    try:
        module_path, attr = spec.split(":", 1)
        module = importlib.import_module(module_path)
        target: Any = getattr(module, attr)
        real_app = target() if callable(target) else target
        app.mount("/realapi", real_app)
        return spec
    except Exception:
        return ""
