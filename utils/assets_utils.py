from pathlib import Path

ASSET_ICON_DIR = Path(__file__).resolve().parent.parent / "assets" / "navbar_icons"


def get_nav_icon(app, name: str) -> str | None:
    """Return an asset URL for the given navbar icon if it exists."""
    png_path = ASSET_ICON_DIR / f"{name}.png"
    if png_path.is_file():
        return app.get_asset_url(f"navbar_icons/{name}.png")
    return None

