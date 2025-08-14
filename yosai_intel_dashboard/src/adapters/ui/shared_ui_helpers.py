from __future__ import annotations

"""Shared helper utilities for UI components.

This module contains small utility functions that are used across multiple UI
components. Placing them here avoids circular imports between component modules
while keeping the helpers in a single location.
"""

from typing import Any, Dict

import dash.html as html
import dash_bootstrap_components as dbc


def create_file_preview_ui(info: Dict[str, Any]) -> html.Div:
    """Return a simple file preview component."""
    rows = info.get("preview_data", [])
    columns = info.get("columns", [])
    table_header = [html.Thead(html.Tr([html.Th(col) for col in columns]))]
    table_body = [
        html.Tbody(
            [html.Tr([html.Td(str(row.get(col, ""))) for col in columns]) for row in rows]
        )
    ]
    return dbc.Table(table_header + table_body, bordered=True, striped=True, hover=True)


__all__ = ["create_file_preview_ui"]

