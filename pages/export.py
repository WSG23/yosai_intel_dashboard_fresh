#!/usr/bin/env python3
"""Export page providing download instructions."""

from dash import html
import dash_bootstrap_components as dbc
from utils.unicode_handler import sanitize_unicode_input


def layout() -> dbc.Container:
    """Simple export page layout."""
    return dbc.Container([], fluid=True)


__all__ = ["layout"]
