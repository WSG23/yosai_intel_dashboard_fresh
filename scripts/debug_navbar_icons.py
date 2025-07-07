#!/usr/bin/env python3
"""Debug helper for navbar icon serving.

Run this script to verify icon files exist and Dash can serve them via
``get_nav_icon``. By default it checks the standard icons defined in the
README but you can pass custom icon names as arguments.
"""
from __future__ import annotations

import argparse
import os
from typing import Iterable

from core.app_factory import create_app
from utils.assets_debug import check_navbar_assets
from utils.assets_utils import get_nav_icon

DEFAULT_ICONS = [
    "dashboard",
    "analytics",
    "graphs",
    "upload",
    "print",
    "settings",
    "logout",
]


def debug_navbar_icons(icon_names: Iterable[str] | None = None) -> None:
    """Print icon existence and test asset URLs."""
    icons = list(icon_names or DEFAULT_ICONS)

    os.environ.setdefault("YOSAI_ENV", "development")
    os.environ.setdefault("SECRET_KEY", "debug")

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


def _main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Debug navbar icons")
    parser.add_argument(
        "icons",
        nargs="*",
        metavar="ICON",
        help="Icon names without .png extension",
    )
    args = parser.parse_args(argv)
    debug_navbar_icons(args.icons or None)


if __name__ == "__main__":
    _main()
