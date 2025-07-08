import os
import shutil
import subprocess

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import pytest
from dash import dcc, html

from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from pages import file_upload
from pages.deep_analytics import layout as analytics_layout
from pages.deep_analytics import register_callbacks as register_analytics_callbacks


def _create_upload_app():
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    coord = TrulyUnifiedCallbacks(app)
    file_upload.register_upload_callbacks(coord)
    app.layout = html.Div([dcc.Location(id="url"), file_upload.layout()])
    return app


def _create_analytics_app():
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    coord = TrulyUnifiedCallbacks(app)
    register_analytics_callbacks(coord)
    app.layout = html.Div([dcc.Location(id="url"), analytics_layout()])
    return app


def test_upload_process_and_layout(dash_duo, tmp_path):
    csv = tmp_path / "sample.csv"
    pd.DataFrame({"a": [1, 2], "b": [3, 4]}).to_csv(csv, index=False)
    app = _create_upload_app()
    dash_duo.start_server(app)
    file_input = dash_duo.find_element("#drag-drop-upload input")
    file_input.send_keys(str(csv))
    dash_duo.wait_for_text_to_contain(
        "#upload-results", "Successfully uploaded", timeout=10
    )


def test_analytics_refresh_sources(dash_duo):
    app = _create_analytics_app()
    dash_duo.start_server(app)
    dash_duo.find_element("#refresh-sources-btn").click()
    dropdown = dash_duo.find_element("#analytics-data-source")
    length = dash_duo.driver.execute_script(
        "return arguments[0].options.length;", dropdown
    )
    assert length >= 1


def test_accessibility_linting(dash_duo):
    app = _create_upload_app()
    dash_duo.start_server(app)
    pa11y = shutil.which("pa11y")
    if not pa11y:
        pytest.skip("pa11y not installed")
    result = subprocess.run(
        [pa11y, dash_duo.server_url], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
