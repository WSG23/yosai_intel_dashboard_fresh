"""Simple performance dashboard placeholder."""

import dash_bootstrap_components as dbc
from dash import html


def layout() -> dbc.Container:
    """Render the performance metrics dashboard."""
    return dbc.Container(
        [html.H2("Performance Dashboard"), html.Div(id="performance-metrics")],
        fluid=True,
    )


__all__ = ["layout"]
