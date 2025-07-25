#!/usr/bin/env python3
"""Debug version to identify base code issues"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import logging

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html

from yosai_intel_dashboard.src.core.truly_unified_callbacks import TrulyUnifiedCallbacks

logger = logging.getLogger(__name__)

# Test basic Dash upload first
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
callbacks = TrulyUnifiedCallbacks(app)

app.layout = html.Div(
    [
        html.H1("Debug Upload Test"),
        dcc.Upload(
            id="upload-test",
            children=html.Div(["Click to Upload"]),
            style={
                "border": "2px dashed #ccc",
                "padding": "20px",
                "text-align": "center",
            },
        ),
        html.Div(id="debug-output"),
    ]
)


@callbacks.callback(
    Output("debug-output", "children"),
    [Input("upload-test", "contents")],
    [State("upload-test", "filename")],
    callback_id="debug_upload",
    component_name="debug_mde",
)
def debug_upload(contents, filename):
    logger.info(
        f"🔍 Callback triggered: contents={contents is not None}, filename={filename}"
    )

    if contents:
        logger.info(f"📁 File received: {filename}")
        return f"File uploaded: {filename}"
    return "No file uploaded"


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app.run_server(debug=True, port=5003)
