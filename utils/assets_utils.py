from pathlib import Path
import logging
from flask import request

ASSET_ICON_DIR = Path(__file__).resolve().parent.parent / "assets" / "navbar_icons"


def get_nav_icon(app, name: str) -> str | None:
    """Return an asset URL for the given navbar icon if it exists."""
    png_path = ASSET_ICON_DIR / f"{name}.png"
    if png_path.is_file():
        try:
            # Always use absolute path to prevent issues when navigating between pages
            base_url = getattr(app.server, 'static_url_path', '') or ''
            if hasattr(app, 'get_asset_url'):
                url = app.get_asset_url(f"navbar_icons/{name}.png")
                if url and not url.startswith('http'):
                    # Ensure absolute path for consistent loading across pages
                    return f"{base_url}/assets/navbar_icons/{name}.png"
                return url
            return f"{base_url}/assets/navbar_icons/{name}.png"
        except Exception as e:
            logging.getLogger(__name__).debug(f"get_asset_url failed for {name}: {e}")
            # Fallback to absolute path
            return f"/assets/navbar_icons/{name}.png"
    return None


def ensure_icon_cache_headers(app):
    """Add cache headers for icon assets to prevent loading issues."""

    @app.server.after_request
    def add_icon_cache_headers(response):
        if response.headers.get("Content-Type", "").startswith("image/") and (
            "/assets/navbar_icons/" in request.path
        ):
            response.headers["Cache-Control"] = "public, max-age=3600"
            response.headers["ETag"] = f'"{hash(request.path)}"'
        return response

    return app


__all__ = ["get_nav_icon", "ensure_icon_cache_headers"]
