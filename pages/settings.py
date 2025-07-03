#!/usr/bin/env python3
"""Settings management page with placeholders."""

from dash import html
import dash_bootstrap_components as dbc
from utils.unicode_handler import sanitize_unicode_input


def _settings_section(title: str) -> dbc.Card:
    """Return a placeholder settings section."""
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


def layout() -> dbc.Container:
    """Settings page layout."""
    sections = dbc.Row(
        [
            dbc.Col(_settings_section("User Preferences"), md=6),
            dbc.Col(_settings_section("System Configuration"), md=6),
        ]
    )

    return dbc.Container([sections], fluid=True)


__all__ = ["layout"]
