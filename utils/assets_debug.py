import logging
from pathlib import Path
from typing import Any, Dict, Iterable

from dash import html  # type: ignore

from core.unicode import safe_unicode_encode

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
        results[safe_unicode_encode(name)] = exists
        if warn and not exists:
            logger.warning(
                "Navbar icon missing: %s",
                safe_unicode_encode(str(path)),
            )
    return results


def debug_dash_asset_serving(app: Any, icon: str = "analytics.png") -> bool:
    """Check if Dash server can serve an icon from the assets directory."""
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
                "Asset serving failed for %s (status %s)", path, res.status_code
            )
        return ok
    except Exception as exc:  # pragma: no cover - best effort
        logger.error("Asset serving test error: %s", exc)
        return False


def navbar_icon(filename: str, alt: str, fallback_text: str, *, warn: bool = True):
    """Return an ``Img`` component or fallback text for missing icons.

    Set ``warn=False`` to suppress the warning log when the icon is missing.
    """
    path = NAVBAR_ICON_DIR / filename
    if path.is_file():
        return html.Img(
            src=f"/assets/navbar_icons/{filename}",
            className="nav-icon nav-icon--image",
            alt=alt,
        )
    if warn:
        logger.warning("Missing navbar icon: %s", safe_unicode_encode(filename))
    return html.Span(fallback_text, className="nav-icon nav-icon--fallback")


__all__ = [
    "check_navbar_assets",
    "debug_dash_asset_serving",
    "navbar_icon",
]
