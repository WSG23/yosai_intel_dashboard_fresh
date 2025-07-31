from __future__ import annotations

import logging

from .app import create_standalone_app
from .config import (
    AI_COLUMN_SERVICE_AVAILABLE,
    AI_DOOR_SERVICE_AVAILABLE,
    CONFIG_SERVICE_AVAILABLE,
    CONTAINER_AVAILABLE,
)


def run_data_enhancer() -> None:
    """Run the standalone data enhancer Dash application."""
    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("🚀 Starting MVP Data Enhancement Tool - Multi-Building Analysis")
    print("=" * 70)
    print(
        f"🔧 AI Column Service: {'✅ Available' if AI_COLUMN_SERVICE_AVAILABLE else '⚠️ Enhanced Fallback'}"
    )
    print(
        f"🚪 AI Door Service: {'✅ Available' if AI_DOOR_SERVICE_AVAILABLE else '⚠️ Enhanced Fallback'}"
    )
    print(
        f"⚙️ Config Service: {'✅ Available' if CONFIG_SERVICE_AVAILABLE else '⚠️ Fallback'}"
    )
    print(
        f"🔌 Service Container: {'✅ Available' if CONTAINER_AVAILABLE else '⚠️ Not Available'}"
    )
    print("=" * 70)

    app = create_standalone_app()
    from .callbacks import register_callbacks

    register_callbacks(app, getattr(app, "_service_container", None))
    app.run_server(debug=True, host="0.0.0.0", port=5003)
