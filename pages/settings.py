#!/usr/bin/env python3
"""Settings management page with live configuration controls."""

import dash_bootstrap_components as dbc
from dash import dcc, html, Output, Input, State
from dash import register_page as dash_register_page
from dash.exceptions import PreventUpdate

from core.theme_manager import sanitize_theme

from config.dynamic_config import dynamic_config
from security.unicode_security_processor import sanitize_unicode_input

from components.ui_component import UIComponent

class SettingsPage(UIComponent):
    """Settings page component."""

    def layout(self) -> dbc.Container:  # type: ignore[override]
        sections = dbc.Row(
            [
                dbc.Col(self._settings_section("User Preferences"), md=6),
                dbc.Col(self._system_config_section(), md=6),

            ]
        )

        return dbc.Container([sections], fluid=True)

    # ------------------------------------------------------------------
    @staticmethod
    def _settings_section(title: str) -> dbc.Card:
        title = sanitize_unicode_input(title)
        return dbc.Card(
            dbc.CardBody(
                [
                    html.H5(title, className="card-title"),
                    html.P("Configuration options coming soon.", className="card-text"),
                ]
            ),
            className="mb-4 settings-section",
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _system_config_section() -> dbc.Card:
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
                ]
            ),
            className="mb-4 settings-section",
        )


_settings_component = SettingsPage()


def load_page(**kwargs) -> SettingsPage:
    """Return a new :class:`SettingsPage` instance."""

    return SettingsPage(**kwargs)


def register_page() -> None:
    """Register the settings page with Dash."""
    dash_register_page(__name__, path="/settings", name="Settings")


def layout() -> dbc.Container:
    """Compatibility wrapper returning the default component layout."""


    return _settings_component.layout()


__all__ = ["SettingsPage", "load_page", "layout", "register_page"]

