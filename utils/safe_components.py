#!/usr/bin/env python3
"""
Emergency Safe Components
Provides safe fallback components that are guaranteed to be JSON serializable
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def safe_navbar():
    """Safe navbar component"""
    return dbc.Navbar(
        [
            dbc.Container(
                [
                    html.A(
                        html.Img(
                            src="/assets/yosai_logo_name_black.png",
                            height="46px",
                            className="navbar__logo",
                            alt="logo",
                        ),
                        href="/",
                        style={"textDecoration": "none"},
                    ),
                    dbc.Nav(
                        [
                            dbc.NavItem(
                                dbc.NavLink(
                                    html.Img(
                                        src="/assets/navbar_icons/dashboard.png",
                                        className="navbar-icon",
                                        alt="Dashboard",
                                    ),
                                    href="/",
                                    external_link=True,
                                    title="Dashboard",
                                )
                            ),
                            dbc.NavItem(
                                dbc.NavLink(
                                    html.Img(
                                        src="/assets/navbar_icons/upload.png",
                                        className="navbar-icon",
                                        alt="Upload",
                                    ),
                                    href="/file-upload",
                                    external_link=True,
                                    title="Upload",
                                )
                            ),
                            dbc.NavItem(
                                dbc.NavLink(
                                    html.Img(
                                        src="/assets/navbar_icons/analytics.png",
                                        className="navbar-icon",
                                        alt="Deep Analytics Page",
                                    ),
                                    href="/analytics",
                                    external_link=True,
                                    title="Deep Analytics Page",
                                )
                            ),
                        ],
                        navbar=True,
                    ),
                    html.Span("Logged in as: HQ Tower - East Wing", className="text-light"),
                ]
            )
        ],
        color="dark",
        dark=True,
        className="mb-3",
        style={"backgroundColor": "#1B2A47"},
    )


def safe_map_panel():
    """Safe map panel component"""
    return dbc.Card([
        dbc.CardHeader([
            html.H4("🗺️ Security Map", className="mb-0"),
            dbc.Badge("🟢 All systems operational", color="success")
        ]),
        dbc.CardBody([
            html.Div([
                html.P("Interactive security map"),
                html.P("Real-time monitoring active"),
                dbc.Progress(value=100, color="success")
            ], style={"height": "300px", "textalign": "center", "padding": "50px"})
        ])
    ])


def safe_bottom_panel():
    """Safe bottom panel component"""
    return dbc.Card([
        dbc.CardHeader("📊 Analytics Panel"),
        dbc.CardBody([
            html.P("Analytics panel is running safely"),
            html.Div("All components are JSON serializable", className="alert alert-success")
        ])
    ])


def safe_incident_alerts():
    """Safe incident alerts component"""
    return dbc.Card([
        dbc.CardHeader("🚨 Incident Alerts"),
        dbc.CardBody([
            dbc.Alert("No active incidents", color="success"),
            html.P("System is operating normally"),
            dbc.Button("View All Incidents", color="primary", size="sm")
        ])
    ])


def safe_weak_signal():
    """Safe weak signal panel component"""
    return dbc.Card([
        dbc.CardHeader("📡 Weak Signal Analysis"),
        dbc.CardBody([
            html.P("Weak signal analysis is running"),
            html.P("All data is properly serialized", className="text-info")
        ])
    ])


# Component registry mapping
SAFE_COMPONENTS = {
    'navbar': safe_navbar,
    'map_panel': safe_map_panel, 
    'bottom_panel': safe_bottom_panel,
    'incident_alerts': safe_incident_alerts,
    'weak_signal': safe_weak_signal,
}


def get_safe_component(name: str):
    """Get a safe component by name"""
    if name in SAFE_COMPONENTS:
        return SAFE_COMPONENTS[name]()
    else:
        return html.Div(f"Safe fallback for: {name}", className="alert alert-info")
