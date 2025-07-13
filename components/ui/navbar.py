#!/usr/bin/env python3
"""Enhanced navbar component with logo and proper import safety."""

import logging
from typing import Any, Optional

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
    return html.Img(src=img_src, className="nav-icon")


def create_navbar_layout() -> Any:
    """Create navbar with logo and proper navigation."""

    if not DBC_AVAILABLE:
        return html.Div("Navbar unavailable - Dash Bootstrap Components not installed")

    try:
        return dbc.Navbar(
            dbc.Container(
                [
                    # Brand with Logo
                    dbc.NavbarBrand(
                        html.Img(
                            src="/assets/yosai_logo_name_white.png",
                            height="40px",
                            style={"filter": "brightness(1)"},
                        ),
                        href="/",
                        className="navbar-brand-link d-flex align-items-center",
                    ),
                    # Navigation Links
                    dbc.Nav(
                        [
                            dbc.NavItem(
                                dcc.Link(
                                    [
                                        html.I(className="fas fa-chart-bar me-2"),
                                        "Analytics",
                                    ],
                                    href="/analytics",
                                    className="nav-link px-3",
                                )
                            ),
                            dbc.NavItem(
                                dcc.Link(
                                    [html.I(className="fas fa-chart-line me-2"), "Graphs"],
                                    href="/graphs",
                                    className="nav-link px-3",
                                )
                            ),
                            dbc.NavItem(
                                dcc.Link(
                                    [html.I(className="fas fa-upload me-2"), "Upload"],
                                    href="/upload",
                                    className="nav-link px-3",
                                )
                            ),
                            dbc.NavItem(
                                dcc.Link(
                                    [
                                        html.I(className="fas fa-download me-2"),
                                        "Export",
                                    ],
                                    href="/export",
                                    className="nav-link px-3",
                                )
                            ),
                            dbc.NavItem(
                                dcc.Link(
                                    [html.I(className="fas fa-cog me-2"), "Settings"],
                                    href="/settings",
                                    className="nav-link px-3",
                                )
                            ),
                        ],
                        navbar=True,
                        className="ms-auto",
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

    except Exception as e:
        logger.error(f"Navbar creation failed: {e}")
        return create_fallback_navbar()


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
                                    "Analytics", href="/analytics", external_link=False
                                )
                            ),
                            dbc.NavItem(
                                dbc.NavLink("Graphs", href="/graphs", external_link=False)
                            ),
                            dbc.NavItem(
                                dbc.NavLink("Upload", href="/upload", external_link=False)
                            ),
                            dbc.NavItem(
                                dbc.NavLink("Export", href="/export", external_link=False)
                        ),
                        dbc.NavItem(
                            dbc.NavLink(
                                "Settings", href="/settings", external_link=False
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
    """Register navbar callbacks (simplified to avoid import errors)."""
    try:
        logger.debug("Navbar callbacks registration skipped - simple navigation mode")
    except Exception as e:
        logger.warning(f"Navbar callback registration failed: {e}")


__all__ = ["create_navbar_layout", "register_navbar_callbacks", "get_simple_icon"]
