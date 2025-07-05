import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html

from core.unified_callback_coordinator import UnifiedCallbackCoordinator
from pages import file_upload


def _create_upload_app():
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    coord = UnifiedCallbackCoordinator(app)
    file_upload.register_callbacks(coord)
    app.layout = html.Div([dcc.Location(id="url"), file_upload.layout()])
    return app


def test_upload_progress_sse(dash_duo, tmp_path):
    csv = tmp_path / "sample.csv"
    pd.DataFrame({"a": [1, 2]}).to_csv(csv, index=False)
    app = _create_upload_app()
    dash_duo.start_server(app)
    assert not dash_duo.find_elements("#upload-progress-interval")
    file_input = dash_duo.find_element("#upload-data input")
    file_input.send_keys(str(csv))
    dash_duo.wait_for_text_to_equal("#upload-progress", "100%", timeout=10)
    logs = dash_duo.driver.execute_script("return window.uploadProgressLog.length")
    assert logs and logs > 3
