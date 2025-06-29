"""
Navigation bar component with grid layout using existing framework
"""

import datetime
from typing import TYPE_CHECKING, Optional, Any, Union
from core.unified_callback_coordinator import UnifiedCallbackCoordinator
from flask_babel import lazy_gettext as _l
from core.plugins.decorators import safe_callback

# Type checking imports
if TYPE_CHECKING:
    import dash_bootstrap_components as dbc
    from dash import html, dcc
    from dash._callback import callback
    from dash.dependencies import Output, Input

# Runtime imports with proper fallbacks
try:
    import dash_bootstrap_components as dbc
    from dash import html, dcc
    from dash._callback import callback
    from dash.dependencies import Output, Input
    DASH_AVAILABLE = True
except ImportError:
    print("Warning: Dash components not available")
    DASH_AVAILABLE = False
    # Create stub classes for type safety
    class _StubComponent:
        def __init__(self, *args, **kwargs):
            pass
        def __call__(self, *args, **kwargs):
            return None
    
    dbc = _StubComponent()
    html = _StubComponent()
    dcc = _StubComponent()
    callback = None
    Output = None
    Input = None


def create_navbar_layout() -> Optional[Any]:
    """Create navbar layout with responsive grid design"""
    if not DASH_AVAILABLE:
        return None

    try:
        return dbc.Navbar(
            [
                dbc.Container(
                    [
                        dcc.Location(id="url-i18n"),
                        # Grid container using existing Bootstrap classes
                        dbc.Row(
                            [
                                # Left Column: Logo Area (clickable)
                                dbc.Col(
                                    [
                                        html.A(
                                            html.Img(
                                                src="/assets/yosai_logo_name_white.png",
                                                height="46px",  # Increased from 45px (2% larger)
                                                className="navbar__logo",
                                            ),
                                            href="/",
                                            style={"textDecoration": "none"}
                                        )
                                    ],
                                    width=3,
                                    className="d-flex align-items-center pl-4",
                                ),

                                # Center Column: Header & Context
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                html.Div(
                                                    id="facility-header",
                                                    children=[
                                                        html.H5(
                                                            _l("Main Panel"),
                                                            className="navbar-title text-primary",
                                                        ),
                                                        html.Small(
                                                            _l("Logged in as: HQ Tower - East Wing"),
                                                            className="navbar-subtitle text-secondary",
                                                        ),
                                                        html.Small(
                                                            id="live-time",
                                                            className="navbar-subtitle text-tertiary",
                                                        ),
                                                    ],
                                                    className="text-center",
                                                )
                                            ]
                                        )
                                    ],
                                    width=6,
                                    className="d-flex align-items-center justify-content-center",
                                ),

                                # Right Column: Navigation Icons + Language Toggle
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                # Navigation Icons
                                                html.Div(
                                                    [
                                                        html.A(
                                                            html.Img(
                                                                src="/assets/navbar_icons/dashboard.png",
                                                                className="navbar-icon",
                                                                alt="Dashboard"
                                                            ),
                                                            href="/",
                                                            className="navbar-nav-link",
                                                            title="Dashboard"
                                                        ),
                                                        html.A(
                                                            html.Img(
                                                                src="/assets/navbar_icons/analytics.png",
                                                                className="navbar-icon",
                                                                alt="Analytics"
                                                            ),
                                                            href="/analytics",
                                                            className="navbar-nav-link",
                                                            title="Analytics"
                                                        ),
                                                        html.A(
                                                            html.Img(
                                                                src="/assets/navbar_icons/upload.png",
                                                                className="navbar-icon",
                                                                alt="Upload"
                                                            ),
                                                            href="/file-upload",
                                                            className="navbar-nav-link",
                                                            title="File Upload"
                                                        ),
                                                        html.A(
                                                            html.Img(
                                                                src="/assets/navbar_icons/print.png",
                                                                className="navbar-icon",
                                                                alt="Export"
                                                            ),
                                                            href="/export",
                                                            className="navbar-nav-link",
                                                            title="Export"
                                                        ),
                                                        html.A(
                                                            html.Img(
                                                                src="/assets/navbar_icons/logout.png",
                                                                className="navbar-icon",
                                                                alt="Logout"
                                                            ),
                                                            href="/login",  # Changed from /logout to /login
                                                            className="navbar-nav-link",
                                                            title="Logout"
                                                        ),
                                                    ],
                                                    className="d-flex align-items-center",

                                                    style={"gap": "1rem"}  # Increased from 0.75rem
                                                ),
                                                dbc.Button(
                                                    "Clear Cache",
                                                    id="clear-cache-btn",
                                                    color="secondary",
                                                    size="sm",
                                                    className="ms-3",
                                                ),

                                                # Language Toggle
                                                html.Div(
                                                    [
                                                        html.Button("EN", className="language-btn active"),
                                                        html.Span("|", className="mx-1"),
                                                        html.Button("JP", className="language-btn"),
                                                    ],
                                                    className="d-flex align-items-center text-sm",
                                                    style={"marginLeft": "2rem"},
                                                    id="language-toggle"
                                                ),
                                                dbc.Button(
                                                    "Settings",
                                                    id="open-settings-btn",
                                                    color="ghost",
                                                    size="sm",
                                                    className="navbar-settings-btn",
                                                    title="Open Settings"
                                                ),
                                            ],
                                            className="d-flex align-items-center justify-content-end",
                                        )
                                    ],
                                    width=3,
                                    className="d-flex align-items-center justify-content-end pr-4",
                                ),
                            ],
                            className="w-100 align-items-center",
                            style={"minHeight": "60px"}
                        ),
                    ],
                    fluid=True,
                )
            ],
            color="primary",
            dark=True,
            sticky="top",
            className="navbar-main"
        )

    except Exception as e:
        print(f"Error creating navbar layout: {e}")
        return _create_fallback_navbar()


def _create_fallback_navbar() -> str:
    """Create fallback navbar when Dash components unavailable"""
    return "Navbar unavailable - Dash components not loaded"


@safe_callback
def register_navbar_callbacks(manager: UnifiedCallbackCoordinator) -> None:
    """Register navbar callbacks for live updates"""
    if not DASH_AVAILABLE or not manager:
        return

    try:
        @manager.register_callback(
            Output("live-time", "children"),
            Input("url-i18n", "pathname"),
            callback_id="navbar_live_time",
            component_name="navbar",
        )
        def update_live_time(pathname: str) -> str:
            """Update live time display"""
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"Live: {current_time}"

        @manager.register_callback(
            Output("language-toggle", "children"),
            Input("language-toggle", "n_clicks"),
            prevent_initial_call=True,
            callback_id="navbar_toggle_language",
            component_name="navbar",
        )
        def toggle_language(n_clicks: Optional[int]) -> list:
            """Toggle between EN and JP languages"""
            if n_clicks and n_clicks % 2 == 1:
                return [
                    html.Button("EN", className="language-btn"),
                    html.Span("|", className="mx-1"),
                    html.Button("JP", className="language-btn active"),
                ]
            else:
                return [
                    html.Button("EN", className="language-btn active"),
                    html.Span("|", className="mx-1"),
                    html.Button("JP", className="language-btn"),
                ]

        @manager.register_callback(
            Output("page-context", "children"),
            Input("url-i18n", "pathname"),
            callback_id="navbar_page_context",
            component_name="navbar",
        )
        def update_page_context(pathname: str) -> str:
            """Update page context based on current route"""
            page_contexts = {
                "/": "Dashboard – Main Operations",
                "/analytics": "Analytics – Data Intelligence",
                "/file-upload": "File Upload – Data Management",
                "/export": "Export – Report Generation",
                "/settings": "Settings – System Configuration",
                "/login": "Login – Authentication"
            }
            return page_contexts.get(pathname, "Dashboard – Main Operations")

    except Exception as e:
        print(f"Error registering navbar callbacks: {e}")


# Export functions for component registry
layout = create_navbar_layout
__all__ = ["create_navbar_layout", "register_navbar_callbacks", "layout"]
