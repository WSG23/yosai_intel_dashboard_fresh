#!/usr/bin/env python3
"""Export page providing download instructions."""

from dash import html
import dash_bootstrap_components as dbc
from utils.unicode_handler import sanitize_unicode_input


def layout() -> dbc.Container:
    """Simple export page layout."""
    header = dbc.Row(
        dbc.Col(
            [
                html.H1("Export", className="text-primary mb-4"),
                html.P(
                    "Use the export menu in the navigation bar to download enhanced data.",
                    className="text-muted",
                ),
            ]
        )
    )

    return dbc.Container([header], fluid=True)


__all__ = ["layout"]
