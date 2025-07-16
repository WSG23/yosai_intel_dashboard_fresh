#!/usr/bin/env python3
"""Enhanced navbar component with logo and improved navigation."""

import logging
from typing import Any, Optional

from core.callback_registry import handle_register_with_deduplication

try:
    import dash
    import dash_bootstrap_components as dbc
    from dash import html

    DBC_AVAILABLE = True
except ImportError:
    DBC_AVAILABLE = False

logger = logging.getLogger(__name__)


def create_navbar_layout() -> Any:
    """Create enhanced navbar with logo and proper navigation."""

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
                            className="me-2",
                            style={"filter": "brightness(1)"},
                            alt="Yōsai logo",
                        ),
                        href="/",
                        className="navbar-brand-link d-flex align-items-center",
                    ),
                    # Navbar Toggler for Mobile
                    dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                    # Collapsible Navigation
                    dbc.Collapse(
                        dbc.Nav(
                            [
                                dbc.NavItem(
                                    dbc.NavLink(
                                        [
                                            html.I(
                                                className="fas fa-chart-bar me-2",
                                                **{"aria-hidden": "true"},
                                            ),
                                            "Analytics",
                                        ],
                                        href="/analytics",
                                        external_link=False,
                                        className="nav-link px-3",
                                        id="nav-analytics",
                                    )
                                ),
                                dbc.NavItem(
                                    dbc.NavLink(
                                        [
                                            html.I(
                                                className="fas fa-chart-line me-2",
                                                **{"aria-hidden": "true"},
                                            ),
                                            "Graphs",
                                        ],
                                        href="/graphs",
                                        external_link=False,
                                        className="nav-link px-3",
                                        id="nav-graphs",
                                    )
                                ),
                                dbc.NavItem(
                                    dbc.NavLink(
                                        [
                                            html.I(
                                                className="fas fa-upload me-2",
                                                **{"aria-hidden": "true"},
                                            ),
                                            "Upload",
                                        ],
                                        href="/upload",
                                        external_link=False,
                                        className="nav-link px-3",
                                        id="nav-upload",
                                    )
                                ),
                                dbc.NavItem(
                                    dbc.NavLink(
                                        [
                                            html.I(
                                                className="fas fa-download me-2",
                                                **{"aria-hidden": "true"},
                                            ),
                                            "Export",
                                        ],
                                        href="/export",
                                        external_link=False,
                                        className="nav-link px-3",
                                        id="nav-export",
                                    )
                                ),
                                dbc.NavItem(
                                    dbc.NavLink(
                                        [
                                            html.I(
                                                className="fas fa-cog me-2",
                                                **{"aria-hidden": "true"},
                                            ),
                                            "Settings",
                                        ],
                                        href="/settings",
                                        external_link=False,
                                        className="nav-link px-3",
                                        id="nav-settings",
                                    )
                                ),
                            ],
                            navbar=True,
                            className="ms-auto",
                        ),
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
            className="navbar navbar-expand-lg fixed-top shadow-sm bg-black",
        )

    except Exception as e:
        logger.error(f"Enhanced navbar creation failed: {e}")
        return create_fallback_navbar()


def create_fallback_navbar():
    """Simple fallback navbar."""
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
    """Register navbar toggle callback for mobile."""
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

    except Exception as e:
        logger.warning(f"Navbar callback registration failed: {e}")


__all__ = ["create_navbar_layout", "register_navbar_callbacks"]
