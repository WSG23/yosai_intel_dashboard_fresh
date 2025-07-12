#!/usr/bin/env python3
"""Settings management page with live configuration controls."""

import dash_bootstrap_components as dbc
from dash import dcc, html, Output, Input, State
from dash import register_page as dash_register_page
from dash.exceptions import PreventUpdate

from core.theme_manager import sanitize_theme

from config.dynamic_config import dynamic_config
from security.unicode_security_processor import sanitize_unicode_input



def register_page() -> None:
    """Register the settings page with Dash."""
    dash_register_page(__name__, path="/settings", name="Settings")


def _user_preferences_section(title: str) -> dbc.Card:
    """Return user preference controls."""
    title = sanitize_unicode_input(title)
    return dbc.Card(
        dbc.CardBody(
            [
                html.H5(title, className="card-title"),
                dbc.Label("Theme", html_for="theme-dropdown", className="fw-bold"),
                dcc.Dropdown(
                    id="theme-dropdown",
                    options=[
                        {"label": "Dark", "value": "dark"},
                        {"label": "Light", "value": "light"},
                        {"label": "High Contrast", "value": "high-contrast"},
                    ],
                    value="dark",
                    clearable=False,
                    className="mb-3",
                ),
            ]
        ),
        className="mb-4 settings-section",
    )


def _system_config_section() -> dbc.Card:
    """Return system configuration with dropdowns for key settings."""

    rate_options = [60, 120, 200, 500, 1000]
    timeout_options = [5, 10, 20, 30, 60]
    batch_options = [1000, 2000, 5000, 10000, 25000]

    return dbc.Card(
        dbc.CardBody(
            [
                html.H5("System Configuration", className="card-title"),
                dbc.Label(
                    "Rate Limit (per minute)",
                    html_for="setting-rate-limit",
                    className="fw-bold",
                ),
                dcc.Dropdown(
                    id="setting-rate-limit",
                    options=[{"label": str(o), "value": o} for o in rate_options],
                    value=dynamic_config.security.rate_limit_requests,
                    clearable=False,
                    className="mb-3",
                ),
                dbc.Label(
                    "DB Connection Timeout",
                    html_for="setting-db-timeout",
                    className="fw-bold",
                ),
                dcc.Dropdown(
                    id="setting-db-timeout",
                    options=[{"label": str(o), "value": o} for o in timeout_options],
                    value=dynamic_config.database.connection_timeout_seconds,
                    clearable=False,
                    className="mb-3",
                ),
                dbc.Label(
                    "Analytics Batch Size",
                    html_for="setting-batch-size",
                    className="fw-bold",
                ),
                dcc.Dropdown(
                    id="setting-batch-size",
                    options=[{"label": str(o), "value": o} for o in batch_options],
                    value=dynamic_config.analytics.batch_size,
                    clearable=False,
                ),
                dbc.Button(
                    "Apply",
                    id="apply-config-btn",
                    color="primary",
                    className="mt-3",
                ),
                html.Div(id="config-update-alert"),
            ]
        ),
        className="mb-4 settings-section",
    )


def layout() -> dbc.Container:
    """Settings page layout."""
    sections = dbc.Row(
        [
            dbc.Col(_user_preferences_section("User Preferences"), md=6),
            dbc.Col(_system_config_section(), md=6),
        ]
    )

    return dbc.Container([sections], fluid=True)


def apply_system_config(rate_limit: int, db_timeout: int, batch_size: int) -> dbc.Alert:
    """Update dynamic configuration and return a success alert."""
    dynamic_config.security.rate_limit_requests = rate_limit
    dynamic_config.database.connection_timeout_seconds = db_timeout
    dynamic_config.analytics.batch_size = batch_size
    return dbc.Alert(
        "Configuration updated successfully.",
        color="success",
        dismissable=True,
        is_open=True,
    )


def register_callbacks(manager) -> None:
    """Register settings callbacks with the given manager."""
    if manager is None:
        return

    @manager.unified_callback(
        Output("config-update-alert", "children"),
        Input("apply-config-btn", "n_clicks"),
        State("setting-rate-limit", "value"),
        State("setting-db-timeout", "value"),
        State("setting-batch-size", "value"),
        callback_id="apply_system_config",
        component_name="settings",
        prevent_initial_call=True,
    )
    def _apply_cfg(n_clicks, rate, timeout, batch):
        if not n_clicks:
            raise PreventUpdate
        return apply_system_config(int(rate), int(timeout), int(batch))

    @manager.unified_callback(
        Output("theme-store", "data"),
        Input("theme-dropdown", "value"),
        callback_id="update_theme_store",
        component_name="settings",
    )
    def _update_theme(value):
        return sanitize_theme(value)

    manager.app.clientside_callback(
        "function(d){if(window.setAppTheme&&d){window.setAppTheme(d);}return '';}",
        Output("theme-dummy-output", "children"),
        Input("theme-store", "data"),
    )


__all__ = [
    "layout",
    "register_page",
    "apply_system_config",
    "register_callbacks",
]
