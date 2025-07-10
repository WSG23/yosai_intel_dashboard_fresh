#!/usr/bin/env python3
"""
Fixed navbar component with proper asset fallback and stability.
Replace existing components/ui/navbar.py entirely.
"""

import logging
from pathlib import Path
from typing import Any, Optional

from dash.development.base_component import Component

import dash_bootstrap_components as dbc
from dash import Input, Output, State, html

from core.unicode import safe_encode_text

logger = logging.getLogger(__name__)

# Asset paths
ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"
NAVBAR_ICON_DIR = ASSETS_DIR / "navbar_icons"


def create_safe_icon(icon_name: str, fa_fallback: str = "file") -> Component:
    """
    Create navbar icon with FontAwesome fallback.
    
    Args:
        icon_name: Name of the icon (without .png extension)
        fa_fallback: FontAwesome icon name to use as fallback
        
    Returns:
        Icon component (image or FontAwesome fallback)
    """
    try:
        icon_path = NAVBAR_ICON_DIR / f"{icon_name}.png"
        
        if icon_path.exists():
            # Use image if it exists
            return html.Img(
                src=f"/assets/navbar_icons/{icon_name}.png",
                className="nav-icon nav-icon--image",
                style={
                    "width": "16px",
                    "height": "16px", 
                    "marginRight": "0.5rem",
                    "verticalAlign": "middle"
                },
                alt=safe_encode_text(icon_name)
            )
        else:
            # FontAwesome fallback
            return html.I(
                className=f"fas fa-{fa_fallback} nav-icon nav-icon--fallback",
                style={
                    "marginRight": "0.5rem",
                    "width": "16px",
                    "textAlign": "center"
                }
            )
            
    except Exception as e:
        logger.warning(f"Icon creation failed for {icon_name}: {e}")
        # Ultimate fallback
        return html.I(
            className=f"fas fa-{fa_fallback} nav-icon nav-icon--fallback",
            style={"marginRight": "0.5rem"}
        )


def create_navbar_layout() -> dbc.Navbar:
    """
    Create stable navbar layout with proper Unicode handling.
    
    Returns:
        Bootstrap navbar component
    """
    try:
        # Safe text encoding
        brand_text = safe_encode_text("🏯 Yōsai Dashboard")
        analytics_text = safe_encode_text("Deep Analytics")
        upload_text = safe_encode_text("Upload Files")
        settings_text = safe_encode_text("Settings")

        navbar = dbc.Navbar(
            [
                dbc.Container(
                    [
                        # Brand
                        dbc.NavbarBrand(
                            [
                                html.Img(
                                    src="/assets/yosai_logo_name_white.png",
                                    height="30px",
                                    className="me-2"
                                ),
                                brand_text
                            ],
                            href="/",
                            className="navbar-brand-link text-decoration-none",
                            external_link=False
                        ),
                        
                        # Mobile toggle
                        dbc.NavbarToggler(
                            id="navbar-toggler",
                            n_clicks=0
                        ),
                        
                        # Collapsible navigation
                        dbc.Collapse(
                            [
                                dbc.Nav(
                                    [
                        # Analytics  
                        dbc.NavItem(
                            dbc.NavLink(
                                [
                                    create_safe_icon("analytics", "chart-bar"),
                                    "Analytics"
                                ],
                                href="/analytics",
                                id="nav-analytics-link",
                                external_link=False,
                                className="nav-link-stable"
                            ),
                            className="nav-item-stable"
                        ),
                        
                        # File Upload
                        dbc.NavItem(
                            dbc.NavLink(
                                [
                                    create_safe_icon("upload", "upload"),
                                    "Upload"
                                ],
                                href="/upload",
                                id="nav-upload-link", 
                                external_link=False,
                                className="nav-link-stable"
                            ),
                            className="nav-item-stable"
                        ),
                        
                        # Export
                        dbc.NavItem(
                            dbc.NavLink(
                                [
                                    create_safe_icon("export", "download"),
                                    "Export"
                                ],
                                href="/export",
                                id="nav-export-link",
                                external_link=False,
                                className="nav-link-stable"
                            ),
                            className="nav-item-stable"
                        ),
                        
                        # Settings
                        dbc.NavItem(
                            dbc.NavLink(
                                [
                                    create_safe_icon("settings", "cog"),
                                    "Settings"
                                ],
                                href="/settings",
                                id="nav-settings-link",
                                external_link=False,
                                className="nav-link-stable"
                            ),
                            className="nav-item-stable"
                        ),
],
                                    navbar=True,
                                    className="ms-auto navbar-nav-stable"
                                )
                            ],
                            id="navbar-collapse",
                            navbar=True,
                            is_open=False
                        ),
                    ],
                    fluid=True,
                    className="navbar-container-stable"
                )
            ],
            color="light",
            dark=False,
            className="shadow-sm navbar-stable fixed-top",
            id="main-navbar",
            sticky="top"
        )

        return navbar

    except Exception as e:
        logger.error(f"Navbar creation failed: {e}")
        # Minimal fallback navbar
        return create_fallback_navbar()


def create_fallback_navbar() -> dbc.Navbar:
    """
    Create minimal fallback navbar when main creation fails.
    
    Returns:
        Simple navbar component
    """
    return dbc.Navbar(
        [
            dbc.Container(
                [
                    dbc.NavbarBrand("Intel Dashboard", href="/"),
                    dbc.Nav(
                        [
                        # Analytics  
                        dbc.NavItem(
                            dbc.NavLink(
                                [
                                    create_safe_icon("analytics", "chart-bar"),
                                    "Analytics"
                                ],
                                href="/analytics",
                                id="nav-analytics-link",
                                external_link=False,
                                className="nav-link-stable"
                            ),
                            className="nav-item-stable"
                        ),
                        
                        # File Upload
                        dbc.NavItem(
                            dbc.NavLink(
                                [
                                    create_safe_icon("upload", "upload"),
                                    "Upload"
                                ],
                                href="/upload",
                                id="nav-upload-link", 
                                external_link=False,
                                className="nav-link-stable"
                            ),
                            className="nav-item-stable"
                        ),
                        
                        # Export
                        dbc.NavItem(
                            dbc.NavLink(
                                [
                                    create_safe_icon("export", "download"),
                                    "Export"
                                ],
                                href="/export",
                                id="nav-export-link",
                                external_link=False,
                                className="nav-link-stable"
                            ),
                            className="nav-item-stable"
                        ),
                        
                        # Settings
                        dbc.NavItem(
                            dbc.NavLink(
                                [
                                    create_safe_icon("settings", "cog"),
                                    "Settings"
                                ],
                                href="/settings",
                                id="nav-settings-link",
                                external_link=False,
                                className="nav-link-stable"
                            ),
                            className="nav-item-stable"
                        ),
],
                        navbar=True,
                        className="ms-auto"
                    ),
                ],
                fluid=True
            )
        ],
        color="light",
        dark=False,
        className="shadow-sm"
    )


def register_navbar_callbacks(callback_manager, service: Optional[Any] = None) -> None:
    """
    Register consolidated navbar callbacks.
    
    Args:
        callback_manager: TrulyUnifiedCallbacks manager
        service: Optional service dependency
    """
    try:
        # Mobile navbar toggle
        @callback_manager.register_handler(
            Output("navbar-collapse", "is_open"),
            [Input("navbar-toggler", "n_clicks")],
            [State("navbar-collapse", "is_open")],
            callback_id="toggle_navbar_collapse",
            component_name="navbar",
        )
        def toggle_navbar_collapse(n_clicks: int, is_open: bool) -> bool:
            """Toggle mobile navbar collapse state."""
            if n_clicks:
                return not is_open
            return is_open

        logger.info("Navbar callbacks registered successfully")

    except Exception as e:
        logger.error(f"Failed to register navbar callbacks: {e}")


__all__ = [
    "create_navbar_layout",
    "register_navbar_callbacks", 
    "create_safe_icon"
]
