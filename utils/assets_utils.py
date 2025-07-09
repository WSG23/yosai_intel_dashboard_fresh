from pathlib import Path
import logging
from flask import request, url_for

ASSET_ICON_DIR = Path(__file__).resolve().parent.parent / "assets" / "navbar_icons"


def get_nav_icon(app, name: str) -> str | None:
    """Return an asset URL for the given navbar icon if it exists."""
    png_path = ASSET_ICON_DIR / f"{name}.png"
    if not png_path.is_file():
        return None

    server = getattr(app, "server", app)

    try:
        with server.test_request_context():
            return url_for("assets", filename=f"navbar_icons/{name}.png")
    except Exception as exc:  # pragma: no cover - best effort
        logging.getLogger(__name__).debug(f"url_for failed for {name}: {exc}")
        return f"/assets/navbar_icons/{name}.png"


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


def ensure_navbar_assets(app=None) -> None:
    """Ensure navbar icons exist or create simple placeholders."""
    required_icons = [
        "analytics.png",
        "graphs.png",
        "export.png",
        "settings.png",
        "upload.png",
    ]
    ASSET_ICON_DIR.mkdir(parents=True, exist_ok=True)

    for icon in required_icons:
        path = ASSET_ICON_DIR / icon
        if path.exists():
            continue
        try:
            from PIL import Image, ImageDraw  # type: ignore

            img = Image.new("RGBA", (24, 24), (100, 100, 100, 255))
            draw = ImageDraw.Draw(img)
            draw.rectangle([4, 4, 20, 20], fill=(255, 255, 255, 255))
            img.save(path)
            logging.getLogger(__name__).info("Created placeholder icon %s", path)
        except Exception:  # pragma: no cover - best effort fallback
            path.touch()
            logging.getLogger(__name__).warning(
                "Created empty placeholder for %s - install Pillow for better icons",
                path,
            )


__all__ = ["get_nav_icon", "ensure_icon_cache_headers", "ensure_navbar_assets"]
