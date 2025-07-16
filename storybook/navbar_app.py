#!/usr/bin/env python3
"""Standalone preview for the Navbar component."""

import dash
import dash_bootstrap_components as dbc
from dash import html

from components.ui.navbar import create_navbar_layout

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div(
    [
        create_navbar_layout(),
        html.Div("Navbar preview", className="p-4"),
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True)
