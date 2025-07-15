#!/usr/bin/env python3
"""Unified configurable navbar component."""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

# Safe imports with fallbacks for environments without Dash
try:
    import dash
    import dash_bootstrap_components as dbc

    html = dash.html
    dcc = dash.dcc
    DBC_AVAILABLE = True
except ImportError:  # pragma: no cover - fallback for docs/tests
    DBC_AVAILABLE = False

    class _Fallback:
        def __getattr__(self, name: str) -> Any:  # pragma: no cover - simple fallback
            return lambda *a, **k: f"{name} unavailable"

    html = _Fallback()
    dbc = _Fallback()
    dcc = _Fallback()

# Default icon class mapping and navigation links
DEFAULT_ICONS: Dict[str, str] = {
    "dashboard": "fas fa-home me-2",
    "analytics": "fas fa-chart-bar me-2",
    "graphs": "fas fa-chart-line me-2",
    "upload": "fas fa-upload me-2",
    "export": "fas fa-download me-2",
    "settings": "fas fa-cog me-2",
}

DEFAULT_LINKS: List[Dict[str, str]] = [
    {"name": "dashboard", "label": "Dashboard", "href": "/dashboard"},
    {"name": "analytics", "label": "Analytics", "href": "/analytics"},
    {"name": "graphs", "label": "Graphs", "href": "/graphs"},
    {"name": "upload", "label": "Upload", "href": "/upload"},
    {"name": "export", "label": "Export", "href": "/export"},
    {"name": "settings", "label": "Settings", "href": "/settings"},
]


def get_simple_icon(name: str, icon_urls: Optional[Dict[str, str]] = None) -> Any:
    """Return an ``html.Img`` element for *name* using ``icon_urls`` or assets."""

    src = None
    if icon_urls:
        src = icon_urls.get(name)
    if src is None:
        src = f"/assets/{name}.png"
    return html.Img(src=src, className="nav-icon", alt=f"{name} icon")


def _build_nav_items(
    links: Iterable[Dict[str, str]], icons: Dict[str, str]
) -> List[Any]:
    items = []
    for link in links:
        icon_class = icons.get(link.get("name", ""))
        icon_elem = (
            html.I(className=icon_class, **{"aria-hidden": "true"})
            if icon_class
            else None
        )
        children = [icon_elem, link["label"]] if icon_elem else link["label"]
        items.append(
            dbc.NavItem(
                dbc.NavLink(
                    children,
                    href=link.get("href", "#"),
                    external_link=False,
                    className="nav-link px-3",
                    id=f"nav-{link.get('name', '')}" if link.get("name") else None,
                )
            )
        )
    return items


def create_navbar_layout(
    links: Optional[Iterable[Dict[str, str]]] = None,
    icons: Optional[Dict[str, str]] = None,
    brand_img: str = "/assets/yosai_logo_name_white.png",
) -> Any:
    """Create a responsive navbar with configurable links and icons."""

    if not DBC_AVAILABLE:
        return html.Div("Navbar unavailable - Dash Bootstrap Components not installed")

    links = list(links) if links is not None else list(DEFAULT_LINKS)
    icons = icons or DEFAULT_ICONS

    try:
        nav_items = _build_nav_items(links, icons)
        return dbc.Navbar(
            dbc.Container(
                [
                    dbc.NavbarBrand(
                        html.Img(
                            src=brand_img,
                            height="40px",
                            style={"margin-right": "10px", "filter": "brightness(1)"},
                            alt="Yōsai logo",
                        ),
                        href="/",
                        className="navbar-brand-link d-flex align-items-center",
                    ),
                    dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                    dbc.Collapse(
                        dbc.Nav(nav_items, navbar=True, className="ms-auto"),
                        id="navbar-collapse",
                        is_open=False,
                        navbar=True,
                    ),
                ],
                fluid=True,
                className="px-4",
            ),
            color="dark",
            dark=True,
            expand="lg",
            className="navbar navbar-expand-lg fixed-top shadow-sm",
            style={"background-color": "#000000"},
        )
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.error("Navbar creation failed: %s", exc)
        return create_fallback_navbar()


def create_fallback_navbar() -> Any:
    """Simple fallback navbar always available."""
    if not DBC_AVAILABLE:
        return html.Div("Simple navbar fallback")

    items = _build_nav_items(DEFAULT_LINKS, DEFAULT_ICONS)
    return dbc.Navbar(
        dbc.Container(
            [
                dbc.NavbarBrand("Dashboard", href="/"),
                dbc.Nav(items, navbar=True, className="ms-auto"),
            ],
            fluid=True,
        ),
        color="dark",
        dark=True,
        className="fixed-top",
    )


def register_navbar_callbacks(
    callback_manager: Any, service: Optional[Any] = None
) -> None:
    """Register mobile toggle callback if Dash is available."""

    if not DBC_AVAILABLE:
        return

    try:
        from core.callback_registry import handle_register_with_deduplication

        @handle_register_with_deduplication(  # type: ignore[misc]
            callback_manager,
            dash.dependencies.Output("navbar-collapse", "is_open"),
            dash.dependencies.Input("navbar-toggler", "n_clicks"),
            dash.dependencies.State("navbar-collapse", "is_open"),
            callback_id="navbar_toggle",
            component_name="navbar",
            prevent_initial_call=True,
            source_module=__name__,
        )
        def toggle_navbar_collapse(n: int, is_open: bool) -> bool:
            if n:
                return not is_open
            return is_open

    except Exception as exc:  # pragma: no cover - environment without callbacks
        logger.warning("Navbar callback registration failed: %s", exc)


__all__ = [
    "create_navbar_layout",
    "register_navbar_callbacks",
    "get_simple_icon",
]
