#!/usr/bin/env python3
"""Graphs visualization page with placeholder content."""

from dash import html, dcc
import dash_bootstrap_components as dbc
from utils import sanitize_unicode_input


def layout() -> dbc.Container:
    """Graphs page layout."""
    header = dbc.Row(
        dbc.Col(
            [
                html.H1("Graphs", className="text-primary mb-4"),
                html.P(
                    "Interactive charts will be integrated here.",
                    className="text-muted",
                ),
            ]
        )
    )

    tabs = dbc.Tabs(
        [
            dbc.Tab(label=sanitize_unicode_input("Line Charts"), tab_id="line"),
            dbc.Tab(label=sanitize_unicode_input("Bar Charts"), tab_id="bar"),
            dbc.Tab(label=sanitize_unicode_input("Other"), tab_id="other"),
        ],
        id="graphs-tabs",
        active_tab="line",
        className="mb-3",
    )

    placeholder = html.Div("Chart placeholders", className="graphs-placeholder")

    return dbc.Container([header, tabs, placeholder], fluid=True)


__all__ = ["layout"]
