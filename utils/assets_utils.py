import logging
from pathlib import Path

from dash import Dash
from flask import request, url_for

from utils.assets_debug import check_navbar_assets

ASSET_ICON_DIR = Path(__file__).resolve().parent.parent / "assets" / "navbar_icons"


def get_nav_icon(app, name: str) -> str | None:
    """Simple icon getter - returns None to force FontAwesome fallback"""
    return None


def ensure_icon_cache_headers(app: Dash) -> Dash:
    """Add cache headers for icon assets to prevent loading issues.

    This registers an ``after_request`` hook on ``app.server`` that sets
    ``Cache-Control`` and ``ETag`` headers for responses under
    ``/assets/navbar_icons``. It helps browsers cache navbar icons instead of
    reloading them on every page.

    Parameters
    ----------
    app : dash.Dash
        The Dash application whose underlying Flask ``server`` should receive
        the headers.

    Returns
    -------
    dash.Dash
        The provided ``app`` for convenience so calls can be chained.

    Examples
    --------
    >>> from dash import Dash
    >>> from utils.assets_utils import ensure_icon_cache_headers
    >>> dash_app = Dash(__name__)
    >>> ensure_icon_cache_headers(dash_app)
    >>> # ``dash_app.server`` will now add caching headers for icon responses
    """

    @app.server.after_request
    def add_icon_cache_headers(response):
        if response.headers.get("Content-Type", "").startswith("image/") and (
            "/assets/navbar_icons/" in request.path
        ):
            response.headers["Cache-Control"] = "public, max-age=3600"
            response.headers["ETag"] = f'"{hash(request.path)}"'
        return response

    return app


def ensure_navbar_assets(app=None) -> dict[str, bool]:
    """Ensure navbar icons exist or create simple placeholders.

    Returns a mapping of icon names to their existence state after the
    creation attempt.
    """
    missing_before = [
        name
        for name in NAVBAR_ICON_NAMES
        if not (ASSET_ICON_DIR / f"{name}.png").exists()
    ]
    if missing_before:
        logging.getLogger(__name__).info(
            f"Attempting to create missing navbar icons: {', '.join(missing_before)}"
        )

    ensure_all_navbar_assets(app)

    summary = check_navbar_assets(NAVBAR_ICON_NAMES, warn=False)
    missing_after = [n for n, ok in summary.items() if not ok]
    if missing_after:
        logging.getLogger(__name__).warning(
            f"Navbar icons still missing: {', '.join(missing_after)}"
        )
    return summary


def create_analytics_icon(path: Path) -> None:
    """Create analytics icon (simple bar chart)."""
    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        bars = [(4, 16, 7, 20), (8, 12, 11, 20), (12, 8, 15, 20), (16, 14, 19, 20)]
        for bar in bars:
            draw.rectangle(bar, fill=(52, 152, 219, 255))
        img.save(path)
    except Exception:
        svg = (
            "<svg width='24' height='24' viewBox='0 0 24 24' fill='#3498db'>"
            "<rect x='4' y='16' width='3' height='4'/><rect x='8' y='12' width='3' height='8'/>"
            "<rect x='12' y='8' width='3' height='12'/><rect x='16' y='14' width='3' height='6'/></svg>"
        )
        path.with_suffix(".svg").write_text(svg)
        path.touch()


def create_graphs_icon(path: Path) -> None:
    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.line(
            [(3, 21), (8, 10), (14, 14), (20, 4)], fill=(46, 204, 113, 255), width=2
        )
        img.save(path)
    except Exception:
        path.touch()


def create_export_icon(path: Path) -> None:
    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.polygon(
            [(12, 3), (20, 11), (14, 11), (14, 21), (10, 21), (10, 11), (4, 11)],
            fill=(231, 76, 60, 255),
        )
        img.save(path)
    except Exception:
        path.touch()


def create_settings_icon(path: Path) -> None:
    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((6, 6, 18, 18), outline=(149, 165, 166, 255), width=2)
        draw.ellipse((10, 10, 14, 14), fill=(149, 165, 166, 255))
        img.save(path)
    except Exception:
        path.touch()


def create_upload_icon(path: Path) -> None:
    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.polygon(
            [(12, 4), (20, 12), (15, 12), (15, 20), (9, 20), (9, 12), (4, 12)],
            fill=(241, 196, 15, 255),
        )
        img.save(path)
    except Exception:
        path.touch()


# Mapping of required navbar icon filenames to their creator functions
NAVBAR_ICONS = {
    "analytics.png": create_analytics_icon,
    "graphs.png": create_graphs_icon,
    "export.png": create_export_icon,
    "settings.png": create_settings_icon,
    "upload.png": create_upload_icon,
}

# List of icon base names without the extension for convenience
NAVBAR_ICON_NAMES = [Path(name).stem for name in NAVBAR_ICONS]


def ensure_all_navbar_assets(app=None) -> None:
    """Simplified - no complex icon generation"""
    ASSET_ICON_DIR.mkdir(parents=True, exist_ok=True)
    logging.getLogger(__name__).info("Asset directory ensured")


def fix_flask_mime_types(app: Dash) -> Dash:
    """Fix CSS MIME type issues"""

    @app.server.after_request
    def fix_mime(response):
        if request.path.endswith(".css"):
            response.headers["Content-Type"] = "text/css; charset=utf-8"
        elif request.path.endswith(".js"):
            response.headers["Content-Type"] = "application/javascript"
        return response

    return app


__all__ = [
    "get_nav_icon",
    "ensure_icon_cache_headers",
    "ensure_navbar_assets",
    "ensure_all_navbar_assets",
    "fix_flask_mime_types",
    "NAVBAR_ICON_NAMES",
]
