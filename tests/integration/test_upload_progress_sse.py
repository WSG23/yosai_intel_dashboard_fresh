import shutil

import dash
import dash_bootstrap_components as dbc
import pytest
from dash import dcc, html

from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks
from tests.utils.builders import DataFrameBuilder, UploadFileBuilder

pytestmark = pytest.mark.usefixtures("fake_dash", "fake_dbc")


@pytest.fixture
def _skip_if_no_chromedriver() -> None:
    if not shutil.which("chromedriver"):
        pytest.skip("chromedriver not installed")


import sys
import types


def _create_upload_app(monkeypatch):
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    coord = TrulyUnifiedCallbacks(app)
    dummy_mod = types.ModuleType(
        "yosai_intel_dashboard.src.components.analytics.real_time_dashboard"
    )
    dummy_mod.RealTimeAnalytics = object
    monkeypatch.setitem(
        sys.modules,
        "yosai_intel_dashboard.src.components.analytics.real_time_dashboard",
        dummy_mod,
    )
    from yosai_intel_dashboard.src.components.file_upload_component import (
        FileUploadComponent,
    )

    comp = FileUploadComponent()
    comp.register_callbacks(coord)
    app.layout = html.Div([dcc.Location(id="url"), comp.layout()])
    return app


def test_upload_progress_sse(_skip_if_no_chromedriver, dash_duo, tmp_path, monkeypatch):
    csv = (
        UploadFileBuilder()
        .with_dataframe(DataFrameBuilder().add_column("a", [1, 2]).build())
        .write_csv(tmp_path / "sample.csv")
    )
    app = _create_upload_app(monkeypatch)
    dash_duo.start_server(app)
    assert not dash_duo.find_elements("#upload-progress-interval")
    assert not dash_duo.find_elements("#progress-done-trigger")
    file_input = dash_duo.find_element("#drag-drop-upload input")
    file_input.send_keys(str(csv))
    dash_duo.wait_for_text_to_equal("#upload-progress", "100%", timeout=10)
    logs = dash_duo.driver.execute_script("return window.uploadProgressLog.length")
    assert logs and logs > 3
