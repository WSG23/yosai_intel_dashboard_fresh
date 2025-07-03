"""
Navigation bar component with grid layout using existing framework
"""

import datetime
from typing import TYPE_CHECKING, Optional, Any, Union
from core.unified_callback_coordinator import UnifiedCallbackCoordinator
from flask_babel import lazy_gettext as _l
from core.plugins.decorators import safe_callback
from core.theme_manager import DEFAULT_THEME, sanitize_theme
from utils import check_navbar_assets, navbar_icon

import logging

logger = logging.getLogger(__name__)

# Type checking imports
if TYPE_CHECKING:
    import dash
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
    logger.info("Warning: Dash components not available")
    DASH_AVAILABLE = False
    from typing import Any

    class _StubModule:
        """Return callable stubs for any requested attribute."""

        def __getattr__(self, name: str) -> Any:  # pragma: no cover - dynamic
            def _stub_component(*args: Any, **kwargs: Any) -> None:
                return None

            return _stub_component

    def _stub_callable(*args: Any, **kwargs: Any) -> None:  # pragma: no cover
        return None

    dbc: Any = _StubModule()
    html: Any = _StubModule()
    dcc: Any = _StubModule()
    callback: Any = _stub_callable
    Output: Any = _stub_callable
    Input: Any = _stub_callable


def create_navbar_layout() -> Optional[Any]:
    """Create navbar layout with responsive grid design"""
    if not DASH_AVAILABLE:
        return None

    try:
        check_navbar_assets(
            [
                "analytics.png",
                "upload.png",
                "print.png",
                "settings.png",
                "logout.png",
            ]
        )
        return dbc.Navbar(
            [
                dbc.Container(
                    [
                        dcc.Location(id="url-i18n"),
                        dcc.Store(id="theme-store", data=DEFAULT_THEME),
                        html.Div(id="theme-dummy-output", style={"display": "none"}),
                        # Grid container using existing Bootstrap classes
                        dbc.Row(
                            [
                                # Left Column: Logo Area (clickable)
                                dbc.Col(
                                    [
                                        html.A(
                                            html.Img(
                                                id="navbar-logo",
                                                src="/assets/yosai_logo_name_white.png" if DEFAULT_THEME in ("dark", "high-contrast") else "/assets/yosai_logo_name_black.png",
                                                height="46px",  # Increased from 45px (2% larger)
                                                className="navbar__logo",
                                                alt="logo",
                                            ),
                                            href="/",
                                            className="navbar-logo-link",
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
                                                            str(_l("Main Panel")),
                                                            className="navbar-title text-primary",
                                                        ),
                                                        html.Small(
                                                            str(
                                                                _l(
                                                                    "Logged in as: HQ Tower - East Wing"
                                                                )
                                                            ),
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
                                                            navbar_icon(
                                                                "dashboard.png",
                                                                "Dashboard",
                                                                "🏠",
                                                            ),
                                                            href="/dashboard",
                                                            className="navbar-nav-link",
                                                            title="Dashboard",
                                                        ),
                                                        html.A(
                                                            navbar_icon(
                                                                "analytics.png",
                                                                "Analytics",
                                                                "📊",
                                                            ),
                                                            href="/analytics",
                                                            className="navbar-nav-link",
                                                            title="Analytics",
                                                        ),
                                                        html.A(
                                                            navbar_icon(
                                                                "graphs.png",
                                                                "Graphs",
                                                                "📈",
                                                            ),
                                                            href="/graphs",
                                                            className="navbar-nav-link",
                                                            title="Graphs",
                                                        ),
                                                        html.A(
                                                            navbar_icon(
                                                                "upload.png",
                                                                "Upload",
                                                                "⬆️",
                                                            ),
                                                            href="/file-upload",
                                                            className="navbar-nav-link",
                                                            title="Upload",
                                                        ),
                                                        dbc.DropdownMenu(
                                                            [
                                                                dbc.DropdownMenuItem(
                                                                    "Export CSV",
                                                                    id="nav-export-csv",
                                                                ),
                                                                dbc.DropdownMenuItem(
                                                                    "Export JSON",
                                                                    id="nav-export-json",
                                                                ),
                                                            ],
                                                            nav=True,
                                                            in_navbar=True,
                                                            label=navbar_icon(
                                                                "print.png",
                                                                "Export",
                                                                "🖨️",
                                                            ),
                                                            toggle_class_name="navbar-nav-link",
                                                            menu_variant="dark",
                                                        ),
                                                        dbc.DropdownMenu(
                                                            [
                                                                dbc.DropdownMenuItem(
                                                                    "Light Mode",
                                                                    id="nav-theme-light",
                                                                ),
                                                                dbc.DropdownMenuItem(
                                                                    "Dark Mode",
                                                                    id="nav-theme-dark",
                                                                ),
                                                            ],
                                                            nav=True,
                                                            in_navbar=True,
                                                            label=navbar_icon(
                                                                "settings.png",
                                                                "Settings",
                                                                "⚙️",
                                                            ),
                                                            toggle_class_name="navbar-nav-link nav-icon-btn",
                                                            menu_variant="dark",
                                                        ),
                                                        html.A(
                                                            navbar_icon(
                                                                "logout.png",
                                                                "Logout",
                                                                "🚪",
                                                            ),
                                                            href="/login",  # Changed from /logout to /login
                                                            className="navbar-nav-link",
                                                            title="Logout",
                                                        ),
                                                    ],
                                                    className="d-flex align-items-center nav-icon-group",
                                                ),
                                                dcc.Download(id="download-csv"),
                                                dcc.Download(id="download-json"),
                                                # Language Toggle
                                                html.Div(
                                                    [
                                                        html.Button(
                                                            "EN",
                                                            className="language-btn active",
                                                            **{
                                                                "aria-label": "Switch to English",
                                                                "aria-pressed": "true",
                                                            },
                                                        ),
                                                        html.Span(
                                                            "|", className="mx-1"
                                                        ),
                                                        html.Button(
                                                            "JP",
                                                            className="language-btn",
                                                            **{
                                                                "aria-label": "Switch to Japanese",
                                                                "aria-pressed": "false",
                                                            },
                                                        ),
                                                    ],
                                                    className="d-flex align-items-center text-sm navbar-language-toggle",
                                                    id="language-toggle",
                                                ),
                                            ],
                                            className="d-flex align-items-center justify-content-end",
                                        )
                                    ],
                                    width=3,
                                    className="d-flex align-items-center justify-content-end pr-4",
                                ),
                            ],
                            className="w-100 align-items-center navbar-row",
                        ),
                    ],
                    fluid=True,
                )
            ],
            dark=True,
            sticky="top",
            className="navbar-main",
        )

    except Exception as e:
        logger.info(f"Error creating navbar layout: {e}")
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
                    html.Button(
                        "EN",
                        className="language-btn",
                        **{
                            "aria-label": "Switch to English",
                            "aria-pressed": "false",
                        },
                    ),
                    html.Span("|", className="mx-1"),
                    html.Button(
                        "JP",
                        className="language-btn active",
                        **{
                            "aria-label": "Switch to Japanese",
                            "aria-pressed": "true",
                        },
                    ),
                ]
            else:
                return [
                    html.Button(
                        "EN",
                        className="language-btn active",
                        **{
                            "aria-label": "Switch to English",
                            "aria-pressed": "true",
                        },
                    ),
                    html.Span("|", className="mx-1"),
                    html.Button(
                        "JP",
                        className="language-btn",
                        **{
                            "aria-label": "Switch to Japanese",
                            "aria-pressed": "false",
                        },
                    ),
                ]

        @manager.register_callback(
            Output("theme-store", "data"),
            [Input("nav-theme-light", "n_clicks"), Input("nav-theme-dark", "n_clicks")],
            prevent_initial_call=True,
            callback_id="navbar_select_theme",
            component_name="navbar",
        )
        def update_theme_store(light: Optional[int], dark: Optional[int]):
            ctx = dash.callback_context
            if not ctx.triggered:
                return dash.no_update
            theme = "dark" if ctx.triggered_id == "nav-theme-dark" else "light"
            if theme not in ALLOWED_THEMES:
                theme = DEFAULT_THEME
            return theme

        manager.app.clientside_callback(
            "function(data){if(window.setAppTheme&&data){window.setAppTheme(data);} return '';}",
            Output("theme-dummy-output", "children"),
            Input("theme-store", "data"),
        )

        # Theme selection dropdown removed

        @manager.register_callback(
            Output("navbar-logo", "src"),
            Input("theme-store", "data"),
            callback_id="navbar_logo_theme",
            component_name="navbar",
        )
        def update_logo(theme: Optional[str]) -> str:
            theme = sanitize_theme(theme)
            if theme in ("dark", "high-contrast"):
                return "/assets/yosai_logo_name_white.png"
            return "/assets/yosai_logo_name_black.png"

        @manager.register_callback(
            Output("download-csv", "data"),
            Input("nav-export-csv", "n_clicks"),
            prevent_initial_call=True,
            callback_id="navbar_export_csv",
            component_name="navbar",
        )
        def export_csv(n_clicks: Optional[int]):
            """Export enhanced data as CSV file."""
            import services.export_service as export_service

            data = export_service.get_enhanced_data()
            csv_str = export_service.to_csv_string(data)
            if not csv_str:
                return dash.no_update
            return dict(content=csv_str, filename="enhanced_data.csv")

        @manager.register_callback(
            Output("download-json", "data"),
            Input("nav-export-json", "n_clicks"),
            prevent_initial_call=True,
            callback_id="navbar_export_json",
            component_name="navbar",
        )
        def export_json(n_clicks: Optional[int]):
            """Export enhanced data as JSON file."""
            import services.export_service as export_service

            data = export_service.get_enhanced_data()
            json_str = export_service.to_json_string(data)
            if not json_str:
                return dash.no_update
            return dict(content=json_str, filename="enhanced_data.json")

        @manager.register_callback(
            Output("page-context", "children"),
            Input("url-i18n", "pathname"),
            callback_id="navbar_page_context",
            component_name="navbar",
        )
        def update_page_context(pathname: str) -> str:
            """Update page context based on current route"""
            page_contexts = {
                "/": "Analytics – Data Intelligence",
                "/analytics": "Analytics – Data Intelligence",
                "/file-upload": "File Upload – Data Management",
                "/export": "Export – Report Generation",
                "/settings": "Settings – System Configuration",
                "/login": "Login – Authentication",
            }
            return page_contexts.get(pathname, "Analytics – Data Intelligence")

    except Exception as e:
        logger.info(f"Error registering navbar callbacks: {e}")


# Export functions for component registry
layout = create_navbar_layout
__all__ = ["create_navbar_layout", "register_navbar_callbacks", "layout"]
