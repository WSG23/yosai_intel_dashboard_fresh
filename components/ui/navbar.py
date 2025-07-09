"""Simple navbar - eliminates complex dependencies"""

import logging
import dash_bootstrap_components as dbc
from dash import dcc, html
from flask_babel import lazy_gettext as _l

logger = logging.getLogger(__name__)

NAVBAR_ICONS = {
    "dashboard": "fas fa-home",
    "analytics": "fas fa-chart-bar",
    "graphs": "fas fa-chart-line",
    "upload": "fas fa-cloud-upload-alt",
    "export": "fas fa-download",
    "settings": "fas fa-cog",
}


def get_simple_icon(name: str) -> html.I:
    icon_class = NAVBAR_ICONS.get(name, "fas fa-circle")
    return html.I(className=f"{icon_class} nav-icon", style={"fontSize": "18px"})


def create_navbar_layout(theme: str = "light"):
    return dbc.Navbar(
        [
            dbc.Container(
                [
                    dcc.Location(id="url-navbar", refresh=False),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.A(
                                        html.Img(
                                            src="/assets/yosai_logo_name_black.png",
                                            height="40px",
                                            alt="Logo",
                                        ),
                                        href="/",
                                        className="navbar-brand-link",
                                    )
                                ],
                                width="auto",
                            ),
                            dbc.Col(
                                [
                                    dbc.Nav(
                                        [
                                            dbc.NavItem(
                                                dbc.NavLink(
                                                    [
                                                        get_simple_icon("dashboard"),
                                                        " Dashboard",
                                                    ],
                                                    href="/dashboard",
                                                )
                                            ),
                                            dbc.NavItem(
                                                dbc.NavLink(
                                                    [
                                                        get_simple_icon("analytics"),
                                                        " Analytics",
                                                    ],
                                                    href="/analytics",
                                                )
                                            ),
                                            dbc.NavItem(
                                                dbc.NavLink(
                                                    [
                                                        get_simple_icon("graphs"),
                                                        " Graphs",
                                                    ],
                                                    href="/graphs",
                                                )
                                            ),
                                            dbc.NavItem(
                                                dbc.NavLink(
                                                    [
                                                        get_simple_icon("upload"),
                                                        " Upload",
                                                    ],
                                                    href="/file-upload",
                                                )
                                            ),
                                            dbc.NavItem(
                                                dbc.NavLink(
                                                    [
                                                        get_simple_icon("settings"),
                                                        " Settings",
                                                    ],
                                                    href="/settings",
                                                )
                                            ),
                                        ],
                                        navbar=True,
                                        className="ms-auto",
                                    )
                                ]
                            ),
                        ]
                    ),
                ]
            )
        ],
        color="light",
        className="shadow-sm",
    )


def register_navbar_callbacks(manager, service=None):
    """Compatibility stub - no callbacks currently needed."""
    manager.navbar_registered = True
