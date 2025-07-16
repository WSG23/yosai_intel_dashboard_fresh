#!/usr/bin/env python3
"""Enhanced navbar component with logo and proper import safety."""

import logging
from typing import Any, Optional, Dict

from core.callback_registry import handle_register_with_deduplication

logger = logging.getLogger(__name__)

# Safe imports with fallbacks
try:
    import dash
    import dash_bootstrap_components as dbc

    html = dash.html
    dcc = dash.dcc
    DBC_AVAILABLE = True
except ImportError:
    DBC_AVAILABLE = False

    # Create fallback objects to prevent unbound variable errors
    class FallbackHtml:
        def __getattr__(self, name):
            return lambda *args, **kwargs: f"HTML component {name} not available"

    class FallbackDbc:
        def __getattr__(self, name):
            return lambda *args, **kwargs: f"DBC component {name} not available"

    class FallbackDcc:
        def __getattr__(self, name):
            return lambda *args, **kwargs: f"DCC component {name} not available"

    html = FallbackHtml()
    dbc = FallbackDbc()
    dcc = FallbackDcc()


def get_simple_icon(name: str):
    """Return an icon for the navbar tests."""
    img_src = f"/assets/{name}.png"
    return html.Img(src=img_src, className="nav-icon", alt=f"{name} icon")


def create_navbar_layout(
    links: Optional[Dict[str, str]] = None,
    icons: Optional[Dict[str, Any]] = None,
) -> Any:
    """Create navbar with logo and optional custom navigation."""

    if not DBC_AVAILABLE:
        return create_fallback_navbar()

    default_links: Dict[str, str] = {
        "Dashboard": "/dashboard",
        "Analytics": "/analytics",
        "Graphs": "/graphs",
        "File Upload": "/upload",
        "Export": "/export",
        "Settings": "/settings",
    }
    nav_links = links or default_links

    default_icons: Dict[str, Any] = {
        "Dashboard": html.I(
            className="fas fa-home me-2",
            **{"aria-hidden": "true", "aria-label": "Dashboard"},
        ),
        "Analytics": html.I(
            className="fas fa-chart-bar me-2",
            **{"aria-hidden": "true", "aria-label": "Analytics"},
        ),
        "Graphs": html.I(
            className="fas fa-chart-line me-2",
            **{"aria-hidden": "true", "aria-label": "Graphs"},
        ),
        "File Upload": html.I(
            className="fas fa-upload me-2",
            **{"aria-hidden": "true", "aria-label": "File Upload"},
        ),
        "Export": html.I(
            className="fas fa-download me-2",
            **{"aria-hidden": "true", "aria-label": "Export"},
        ),
        "Settings": html.I(
            className="fas fa-cog me-2",
            **{"aria-hidden": "true", "aria-label": "Settings"},
        ),
    }
    icon_map = {**default_icons, **(icons or {})}

    navbar = None
    try:
        nav_items = []
        for name, href in nav_links.items():
            icon = icon_map.get(name)
            children = [icon, name] if icon is not None else [name]
            nav_items.append(
                dbc.NavItem(
                    dcc.Link(
                        children,
                        href=href,
                        className="nav-link px-3",
                        **{"aria-label": name},
                    )
                )
            )

        navbar = dbc.Navbar(
            dbc.Container(
                [
                    # Brand with Logo
                    dbc.NavbarBrand(
                        html.Img(
                            src="/assets/yosai_logo_name_white.png",
                            height="40px",
                            style={"filter": "brightness(1)"},
                            alt="Yōsai logo",
                        ),
                        href="/",
                        className="navbar-brand-link d-flex align-items-center",
                    ),
                    # Navigation Links
                    dbc.Nav(nav_items, navbar=True, className="ms-auto"),
                ],
                fluid=True,
                className="px-4",
            ),
            color="dark",
            dark=True,
            expand="lg",
            className="navbar navbar-expand-lg navbar-stable bg-gray-900",
        )

    except Exception as e:  # pragma: no cover - defensive
        logger.error(f"Navbar creation failed: {e}")
        navbar = create_fallback_navbar()

    return navbar


def create_fallback_navbar():
    """Simple fallback navbar that always works."""
    if not DBC_AVAILABLE:
        return html.Div("Simple navbar fallback")

    return dbc.Navbar(
        dbc.Container(
            [
                dbc.NavbarBrand("Dashboard", href="/"),
                dbc.Nav(
                    [
                        dbc.NavItem(
                            dbc.NavLink(
                                "Analytics",
                                href="/analytics",
                                external_link=False,
                            )
                        ),
                        dbc.NavItem(
                            dbc.NavLink(
                                "Graphs",
                                href="/graphs",
                                external_link=False,
                            )
                        ),
                        dbc.NavItem(
                            dbc.NavLink(
                                "Upload",
                                href="/upload",
                                external_link=False,
                            )
                        ),
                        dbc.NavItem(
                            dbc.NavLink(
                                "Export",
                                href="/export",
                                external_link=False,
                            )
                        ),
                        dbc.NavItem(
                            dbc.NavLink(
                                "Settings",
                                href="/settings",
                                external_link=False,
                            )
                        ),
                    ],
                    navbar=True,
                    className="ms-auto",
                ),
            ],
            fluid=True,
        ),
        color="dark",
        dark=True,
        className="fixed-top",
    )


def register_navbar_callbacks(callback_manager, service: Optional[Any] = None) -> None:
    """Register navbar toggle callback when Dash is available."""
    if not DBC_AVAILABLE:
        logger.debug("Navbar callbacks registration skipped - Dash unavailable")
        return

    try:

        @handle_register_with_deduplication(
            callback_manager,
            dash.dependencies.Output("navbar-collapse", "is_open"),
            dash.dependencies.Input("navbar-toggler", "n_clicks"),
            dash.dependencies.State("navbar-collapse", "is_open"),
            callback_id="navbar_toggle",
            component_name="navbar",
            prevent_initial_call=True,
            source_module=__name__,
        )
        def toggle_navbar_collapse(n, is_open):
            if n:
                return not is_open
            return is_open

    except Exception as e:  # pragma: no cover - defensive
        logger.warning(f"Navbar callback registration failed: {e}")


__all__ = ["create_navbar_layout", "register_navbar_callbacks", "get_simple_icon"]
