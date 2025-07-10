"""Entry point for the deep analytics Dash page."""

from dash import register_page as dash_register_page

from .layout import layout

def register_page() -> None:
    """Register the analytics page after Dash initialization."""
    dash_register_page(
        __name__, path="/analytics", name="Analytics", aliases=["/", "/dashboard"]
    )

__all__ = ["layout", "register_page"]
