import logging
from pathlib import Path
from typing import Iterable, Dict, Any
import base64
from .unicode_utils import safe_unicode_encode

from dash import html  # type: ignore

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
NAVBAR_ICON_DIR = ASSETS_DIR / "navbar_icons"

# Base64 encoded fallback icons so binary files are not required in the repo
INLINE_NAVBAR_ICONS = {
    "dashboard.png": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAAqklEQVR4nO3YQQrCMABFwSre/8q6FwpB2kwkb9bVPj+SRY4jSZLs6jHwzPv2ivud/s7nzIoVNYAO0F4/fGbk3Bj1fb5c9d3D59b2/4AG0AFaA+gArQF0gNYAOkBrAB2gNYAO0BpAB2gNoAO07QfoWnxmxYoaQAdoXYtf9MK/1QA6QGsAHaA1gA7QGkAHaA2gA7QG0AFaA+gArQF0gNat8MyKFTWADkiSJMwHw4oHZO7ZYxkAAAAASUVORK5CYII=",
    "graphs.png": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAABR0lEQVR4nO2ZWxLCIBAEife/c/yiVGoJOzz2YU1/pZSQbDMYgqUQQgghhBBCCCGEEEIIISQBd+cY4tpwIx70CobreS3eSDTgJGQUMCoSkpBNgLY4tYRsAiSuIs99lYRMAqSCrs7x0zk/ZBGgjTQsIYsAid4jD5KQQcAo+hLt99320QVMr/DKp+hHWdEFSCCrvWHbyAJmog8TVcBK9CGiCpA48uIWUYBJ9Cu7BOyKrFn0KysC2pu9hc92cHTPYqXzUbFo36bRr8wmQDPSSCLMo1/Z9RvwNFKzU8Nku27mIm0xbR/o1HCJfuXEY7C3QVH5ToRb9CurP1Sa89EiTXeqLRZCo0S0bU1BBMyMfts+3P8QHkvhnggXOdqLro7+qG+3ZER4GXKdFhoBJ0ffnQgJcGUk4K9HvxQm4FHA348+gvuanRBCCNnPGyi5LzwmT2G3AAAAAElFTkSuQmCC",
}


def check_navbar_assets(required: Iterable[str]) -> Dict[str, bool]:
    """Return mapping of required icon names to existence state."""
    results: Dict[str, bool] = {}
    for name in required:
        path = NAVBAR_ICON_DIR / name
        exists = path.is_file()
        results[safe_unicode_encode(name)] = exists
        if not exists:
            logger.warning("Navbar icon missing: %s", safe_unicode_encode(str(path)))
    return results


def debug_dash_asset_serving(app: Any, icon: str = "analytics.png") -> bool:
    """Check if Dash server can serve an icon from the assets directory."""
    path = f"/assets/navbar_icons/{icon}"
    try:
        client = app.server.test_client()
        res = client.get(path)
        ok = res.status_code == 200
        if not ok:
            logger.warning(
                "Asset serving failed for %s (status %s)", path, res.status_code
            )
        return ok
    except Exception as exc:  # pragma: no cover - best effort
        logger.error("Asset serving test error: %s", exc)
        return False


def navbar_icon(filename: str, alt: str, fallback_text: str):
    """Return an ``Img`` component or fallback text for missing icons."""
    path = NAVBAR_ICON_DIR / filename
    if path.is_file():
        return html.Img(
            src=f"/assets/navbar_icons/{filename}",
            className="nav-icon",
            alt=alt,
        )
    if filename in INLINE_NAVBAR_ICONS:
        return html.Img(src=INLINE_NAVBAR_ICONS[filename], className="nav-icon", alt=alt)
    logger.warning("Missing navbar icon: %s", safe_unicode_encode(filename))
    return html.Span(fallback_text, className="nav-icon")


__all__ = [
    "check_navbar_assets",
    "debug_dash_asset_serving",
    "navbar_icon",
]
