#!/usr/bin/env python3
"""Enhanced navbar component with logo."""

import logging
from typing import Optional, Any

try:
    import dash_bootstrap_components as dbc
    from dash import html
    DBC_AVAILABLE = True
except ImportError:
    DBC_AVAILABLE = False

logger = logging.getLogger(__name__)

def create_navbar_layout() -> Any:
    """Create navbar with logo and proper navigation."""
    
    if not DBC_AVAILABLE:
        return html.Div("Navbar unavailable")
    
    try:
        return dbc.Navbar(
            dbc.Container(
                [
                    # Brand with Logo
                    dbc.NavbarBrand(
                        html.Img(
                            src="/assets/yosai_logo_name_white.png",
                            height="40px",
                            style={"filter": "brightness(1)"}
                        ),
                        href="/",
                        className="navbar-brand-link d-flex align-items-center"
                    ),
                    
                    # Navigation Links
                    dbc.Nav(
                        [
                            dbc.NavItem(
                                dbc.NavLink(
                                    [
                                        html.I(className="fas fa-chart-bar me-2"),
                                        "Analytics"
                                    ],
                                    href="/analytics",
                                    external_link=False,
                                    className="nav-link px-3"
                                )
                            ),
                            dbc.NavItem(
                                dbc.NavLink(
                                    [
                                        html.I(className="fas fa-upload me-2"),
                                        "Upload"
                                    ],
                                    href="/upload",
                                    external_link=False,
                                    className="nav-link px-3"
                                )
                            ),
                            dbc.NavItem(
                                dbc.NavLink(
                                    [
                                        html.I(className="fas fa-download me-2"),
                                        "Export"
                                    ],
                                    href="/export",
                                    external_link=False,
                                    className="nav-link px-3"
                                )
                            ),
                            dbc.NavItem(
                                dbc.NavLink(
                                    [
                                        html.I(className="fas fa-cog me-2"),
                                        "Settings"
                                    ],
                                    href="/settings",
                                    external_link=False,
                                    className="nav-link px-3"
                                )
                            ),
                        ],
                        navbar=True,
                        className="ms-auto"
                    )
                ],
                fluid=True,
                className="px-4"
            ),
            color="dark",
            dark=True,
            expand="lg",
            className="navbar navbar-expand-lg fixed-top shadow-sm",
            style={"background-color": "#000000"}
        )
        
    except Exception as e:
        logger.error(f"Navbar creation failed: {e}")
        return create_fallback_navbar()

def create_fallback_navbar():
    """Simple fallback navbar."""
    return dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand("Dashboard", href="/"),
            dbc.Nav([
                dbc.NavItem(dbc.NavLink("Analytics", href="/analytics", external_link=False)),
                dbc.NavItem(dbc.NavLink("Upload", href="/upload", external_link=False)),
                dbc.NavItem(dbc.NavLink("Export", href="/export", external_link=False)),
                dbc.NavItem(dbc.NavLink("Settings", href="/settings", external_link=False)),
            ], navbar=True, className="ms-auto")
        ], fluid=True),
        color="dark", dark=True, className="fixed-top"
    )

def register_navbar_callbacks(callback_manager, service: Optional[Any] = None) -> None:
    """Register navbar callbacks (simplified to avoid import errors)."""
    try:
        logger.debug("Navbar callbacks registration skipped - simple navigation mode")
    except Exception as e:
        logger.warning(f"Navbar callback registration failed: {e}")

__all__ = ["create_navbar_layout", "register_navbar_callbacks"]
