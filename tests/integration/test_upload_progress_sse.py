import pytest
import dash
import dash_bootstrap_components as dbc
from tests.utils.builders import DataFrameBuilder, UploadFileBuilder
from dash import dcc, html

from core.truly_unified_callbacks import TrulyUnifiedCallbacks

from pages import file_upload

pytestmark = pytest.mark.usefixtures("fake_dash", "fake_dbc")


def _create_upload_app():
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    coord = TrulyUnifiedCallbacks(app)
    file_upload.register_upload_callbacks(coord)
    app.layout = html.Div([dcc.Location(id="url"), file_upload.layout()])
    return app


def test_upload_progress_sse(dash_duo, tmp_path):
    csv = UploadFileBuilder().with_dataframe(
        DataFrameBuilder().add_column("a", [1, 2]).build()
    ).write_csv(tmp_path / "sample.csv")
    app = _create_upload_app()
    dash_duo.start_server(app)
    assert not dash_duo.find_elements("#upload-progress-interval")
    file_input = dash_duo.find_element("#drag-drop-upload input")
    file_input.send_keys(str(csv))
    dash_duo.wait_for_text_to_equal("#upload-progress", "100%", timeout=10)
    logs = dash_duo.driver.execute_script("return window.uploadProgressLog.length")
    assert logs and logs > 3
