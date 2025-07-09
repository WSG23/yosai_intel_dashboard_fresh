"""Entry point for the deep analytics Dash page."""

from dash import register_page

from .deep_analytics import layout

register_page(
    __name__, path="/analytics", name="Analytics", aliases=["/", "/dashboard"]
)

__all__ = ["layout"]
