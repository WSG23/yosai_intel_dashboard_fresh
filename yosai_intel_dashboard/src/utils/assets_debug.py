#!/usr/bin/env python3
"""Debug utilities for Dash asset serving with safe imports."""

from __future__ import annotations

try:
    from dash import get_asset_url, html  # type: ignore

    DASH_AVAILABLE = True
except ImportError:
    # Provide fallback for when dash is not available
    DASH_AVAILABLE = False
    html = None

import logging
from pathlib import Path
from typing import Any, Dict, Iterable

from yosai_intel_dashboard.src.core.unicode import safe_encode_text

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
NAVBAR_ICON_DIR = ASSETS_DIR / "navbar_icons"


def check_navbar_assets(
    required: Iterable[str], *, warn: bool = True
) -> Dict[str, bool]:
    """Return mapping of required icon names to existence state.

    ``required`` should contain icon base names **without** the ``.png``
    extension. The function appends ``.png`` automatically. Set ``warn=False``
    to suppress warning logs for missing icons.
    """

    results: Dict[str, bool] = {}
    for name in required:
        filename = f"{name}.png"
        path = NAVBAR_ICON_DIR / filename
        exists = path.is_file()
        results[safe_encode_text(name)] = exists
        if warn and not exists:
            logger.warning(f"Navbar icon missing: {safe_encode_text(str(path))}")
    return results


def debug_dash_asset_serving(app: Any, icon: str = "analytics.png") -> bool:
    """Check if Dash server can serve an icon from the assets directory."""

    if hasattr(app, "get_asset_url"):
        path = app.get_asset_url(f"navbar_icons/{icon}")
    else:
        path = f"/assets/navbar_icons/{icon}"

    # Skip probe when the icon file is missing.  This avoids unnecessary
    # network requests during startup when optional icons have been removed.
    if not (NAVBAR_ICON_DIR / icon).is_file():  # pragma: no cover - early exit
        return False

    try:
        client = app.server.test_client()
        res = client.get(path)
        ok = res.status_code == 200
        if not ok:
            logger.warning(
                f"Asset serving failed for {path} (status {res.status_code})"
            )
        return ok
    except Exception as exc:  # pragma: no cover - best effort
        logger.error(f"Asset serving test error: {exc}")
        return False


def log_asset_info(icon: str) -> None:
    """Log whether a navbar icon file exists."""
    path = NAVBAR_ICON_DIR / icon
    logger.info(f"Icon path {path} exists={path.is_file()}")


def navbar_icon(filename: str, alt: str, fallback_text: str, *, warn: bool = True):
    """Return an ``Img`` component or fallback text for missing icons.

    Set ``warn=False`` to suppress the warning log when the icon is missing.
    """
    path = NAVBAR_ICON_DIR / filename
    if path.is_file():
        src = (
            get_asset_url(f"navbar_icons/{filename}")
            if DASH_AVAILABLE
            else f"/assets/navbar_icons/{filename}"
        )
        return html.Img(
            src=src,
            className="nav-icon nav-icon--image",
            alt=alt,
        )
    if warn:
        logger.warning(f"Missing navbar icon: {safe_encode_text(filename)}")
    return html.Span(fallback_text, className="nav-icon nav-icon--fallback")


__all__ = [
    "check_navbar_assets",
    "debug_dash_asset_serving",
    "log_asset_info",
    "navbar_icon",
]
