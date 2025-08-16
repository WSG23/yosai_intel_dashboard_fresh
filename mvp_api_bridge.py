import sys, importlib
from typing import Optional
from fastapi import FastAPI
def mount_real(app: FastAPI, spec: str) -> Optional[str]:
    if not spec:
        return None
    try:
        real = None
        if ":" in spec:
            mod, fn = spec.split(":")
            m = importlib.import_module(mod)
            factory = getattr(m, fn)
            real = factory()
        else:
            m = importlib.import_module(spec)
            for attr in ("app","api","application"):
                if hasattr(m, attr):
                    real = getattr(m, attr)
                    break
        if real is None:
            return None
        app.mount("/realapi", real)
        return spec
    except Exception as e:
        sys.stderr.write(f"[mvp_bridge] mount failed for {spec}: {e}\n")
        return None
