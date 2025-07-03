import logging
from pathlib import Path
from typing import Iterable, Dict, Any
from .unicode_utils import safe_unicode_encode

from dash import html  # type: ignore

logger = logging.getLogger(__name__)

ASSETS_DIR = Path("assets")
NAVBAR_ICON_DIR = ASSETS_DIR / "navbar_icons"


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
            src=f"/assets/navbar_icons/{filename}", className="navbar-icon", alt=alt
        )
    logger.warning("Missing navbar icon: %s", safe_unicode_encode(filename))
    return html.Span(fallback_text, className="navbar-icon-fallback")


__all__ = [
    "check_navbar_assets",
    "debug_dash_asset_serving",
    "navbar_icon",
]
