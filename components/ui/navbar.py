#!/usr/bin/env python3
"""
Fixed navbar component using existing TrulyUnifiedCallbacks system.
Resolves flash/disappear issues on upload file link clicks.
"""

import dash_bootstrap_components as dbc
from dash import html, Input, Output, State
from typing import Optional, Any
import logging

from core.unicode import safe_encode_text
from utils.assets_debug import navbar_icon

logger = logging.getLogger(__name__)


def get_simple_icon(icon_name: str) -> html.I:
    """Get Unicode-safe icon for navbar using existing assets system."""
    try:
        # Use existing navbar_icon function with fallback
        return navbar_icon(f"{icon_name}.png", icon_name, "📁", warn=False)
    except Exception as e:
        logger.warning(f"Icon creation failed for {icon_name}: {e}")
        # Fallback to simple HTML icon
        return html.I(className=f"fas fa-{icon_name}")


def create_navbar_layout() -> dbc.Navbar:
    """Create Unicode-safe navbar layout."""
    try:
        # Unicode-safe text processing using existing system
        upload_text = safe_encode_text(" Upload")
        settings_text = safe_encode_text(" Settings")
        analytics_text = safe_encode_text(" Analytics")
        brand_text = safe_encode_text("Dashboard")

        navbar = dbc.Navbar(
            [
                dbc.Container(
                    [
                        dbc.NavbarBrand(
                            brand_text,
                            className="navbar-brand-link",
                            href="/",
                        ),
                        dbc.NavbarToggler(id="navbar-toggler"),
                        dbc.Collapse(
                            [
                                dbc.Nav(
                                    [
                                        dbc.NavItem(
                                            dbc.NavLink(
                                                [
                                                    get_simple_icon("analytics"),
                                                    analytics_text,
                                                ],
                                                href="/analytics",
                                                id="nav-analytics-link",
                                                external_link=False,
                                            )
                                        ),
                                        dbc.NavItem(
                                            dbc.NavLink(
                                                [
                                                    get_simple_icon("upload"),
                                                    upload_text,
                                                ],
                                                href="/file-upload",
                                                id="nav-upload-link",
                                                external_link=False,
                                            )
                                        ),
                                        dbc.NavItem(
                                            dbc.NavLink(
                                                [
                                                    get_simple_icon("settings"),
                                                    settings_text,
                                                ],
                                                href="/settings",
                                                id="nav-settings-link",
                                                external_link=False,
                                            )
                                        ),
                                    ],
                                    navbar=True,
                                    className="ms-auto",
                                )
                            ],
                            id="navbar-collapse",
                            navbar=True,
                        ),
                    ],
                    fluid=True,
                )
            ],
            color="light",
            dark=False,
            className="shadow-sm navbar-stable",
            id="main-navbar",
        )

        return navbar

    except Exception as e:
        logger.error(f"Navbar creation failed: {e}")
        # Return minimal fallback navbar
        return dbc.Navbar(
            [
                dbc.Container(
                    [
                        dbc.NavbarBrand("Dashboard", href="/"),
                        dbc.Nav(
                            [
                                dbc.NavItem(
                                    dbc.NavLink(
                                        "Upload",
                                        href="/file-upload",
                                        external_link=False,
                                    )
                                ),
                            ],
                            navbar=True,
                        ),
                    ]
                )
            ]
        )


def register_navbar_callbacks(manager, service: Optional[Any] = None) -> None:
    """Register navbar callbacks using TrulyUnifiedCallbacks system."""
    try:
        # Register toggle callback using existing system
        @manager.unified_callback(
            Output("navbar-collapse", "is_open"),
            Input("navbar-toggler", "n_clicks"),
            State("navbar-collapse", "is_open"),
            callback_id="navbar_toggle",
            component_name="navbar",
            prevent_initial_call=True,
        )
        def toggle_navbar_collapse(n_clicks, is_open):
            """Toggle navbar collapse state."""
            if n_clicks:
                return not is_open
            return is_open

        # Mark as registered
        if hasattr(manager, "navbar_registered"):
            manager.navbar_registered = True

        logger.info(
            "Navbar callbacks registered successfully with TrulyUnifiedCallbacks"
        )

    except Exception as e:
        logger.error(f"Navbar callback registration failed: {e}")
        # Fallback: just mark as registered
        if hasattr(manager, "navbar_registered"):
            manager.navbar_registered = True


__all__ = ["create_navbar_layout", "register_navbar_callbacks", "get_simple_icon"]
