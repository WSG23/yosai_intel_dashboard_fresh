from pathlib import Path
import logging

ASSET_ICON_DIR = Path(__file__).resolve().parent.parent / "assets" / "navbar_icons"


def get_nav_icon(app, name: str) -> str | None:
    """Return an asset URL for the given navbar icon if it exists."""
    png_path = ASSET_ICON_DIR / f"{name}.png"
    if png_path.is_file():
        try:
            if hasattr(app, "get_asset_url"):
                url = app.get_asset_url(f"navbar_icons/{name}.png")
                if url:
                    return url
            return f"/assets/navbar_icons/{name}.png"
        except Exception as e:  # pragma: no cover - best effort
            logging.getLogger(__name__).debug(
                f"get_asset_url failed for {name}: {e}"
            )
            return f"/assets/navbar_icons/{name}.png"
    return None
