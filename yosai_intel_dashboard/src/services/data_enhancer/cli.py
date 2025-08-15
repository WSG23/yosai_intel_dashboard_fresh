from __future__ import annotations
import os
from typing import Any

def run_data_enhancer(*args: Any, **kwargs: Any) -> None:
    """
    Optional UI runner for the Data Enhancer.

    By default, does nothing in server/API contexts to avoid importing Dash.
    Set ENABLE_DATA_ENHANCER_UI=1 to actually start the UI and import the app.
    """
    if os.getenv("ENABLE_DATA_ENHANCER_UI", "0") != "1":
        # Headless/server mode: skip UI entirely.
        return

    # Import lazily so normal imports of this package don't drag in Dash.
    from .app import create_standalone_app  # type: ignore

    app = create_standalone_app()
    # If the factory returns a Dash/FastAPI-like object, prefer its own run/start.
    # Fallback to a simple server.run if it exposes one.
    if hasattr(app, "run"):
        app.run()
    elif hasattr(app, "server") and hasattr(app.server, "run"):
        app.server.run()
    else:
        # Nothing to run; silently exit in UI mode (or raise if you prefer)
        pass
