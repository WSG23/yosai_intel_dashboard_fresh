#!/usr/bin/env python3
"""Dashboard overview page with placeholder metrics."""

from dash import html
import dash_bootstrap_components as dbc
from utils.unicode_handler import sanitize_unicode_input


def _metric_card(title: str, value: str) -> dbc.Col:
    """Return a simple metric card."""
    title = sanitize_unicode_input(title)
    value = sanitize_unicode_input(value)
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5(title, className="card-title"),
                    html.H2(value, className="card-text"),
                ]
            ),
            className="mb-4",
        ),
        md=4,
    )


def layout() -> dbc.Container:
    """Dashboard page layout."""
    header = dbc.Row(
        dbc.Col(
            [
                html.H1("Security Dashboard", className="text-primary mb-4"),
                html.P(
                    "Real-time security metrics will appear here.",
                    className="text-muted",
                ),
            ]
        )
    )

    metrics = dbc.Row(
        [
            _metric_card("Active Alerts", "0"),
            _metric_card("Devices Online", "0"),
            _metric_card("Last Update", "N/A"),
        ],
        className="gy-4",
    )

    return dbc.Container([header, metrics], fluid=True)


__all__ = ["layout"]
