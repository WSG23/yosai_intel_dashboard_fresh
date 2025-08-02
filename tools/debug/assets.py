from __future__ import annotations

"""Asset debugging helpers."""

import os
from typing import Iterable

from yosai_intel_dashboard.src.core.app_factory import create_app
from yosai_intel_dashboard.src.core.env_validation import validate_env
from yosai_intel_dashboard.src.utils.assets_debug import check_navbar_assets, debug_dash_asset_serving
from yosai_intel_dashboard.src.utils.assets_utils import get_nav_icon

DEFAULT_ICONS = [
    "analytics",
    "graphs",
    "export",
    "upload",
    "print",
    "settings",
    "logout",
]


def debug_navbar_icons(icon_names: Iterable[str] | None = None) -> None:
    """Print icon existence and test asset URLs."""
    icons = list(icon_names or DEFAULT_ICONS)

    os.environ.setdefault("YOSAI_ENV", "development")
    validate_env(["SECRET_KEY"])

    app = create_app(mode="simple")
    results = check_navbar_assets(icons, warn=False)
    client = app.server.test_client()

    for name in icons:
        exists = results.get(name, False)
        url = get_nav_icon(app, name)
        status = None
        if url:
            try:
                res = client.get(url)
                status = res.status_code
            except Exception:
                status = "error"
        print(f"{name}: file={'yes' if exists else 'no'}, url={url!r}, status={status}")


__all__ = ["debug_navbar_icons", "check_navbar_assets", "debug_dash_asset_serving"]
