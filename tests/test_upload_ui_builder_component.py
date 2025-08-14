import pandas as pd
import pytest

from yosai_intel_dashboard.src.adapters.ui.components import UploadUIBuilder

pytestmark = pytest.mark.usefixtures("fake_dash", "fake_dbc")


def test_build_success_alert():
    ui = UploadUIBuilder()
    alert = ui.build_success_alert("x.csv", 1, 1)
    assert hasattr(alert, "children")


def test_build_file_preview_component():
    df = pd.DataFrame({"a": [1]})
    ui = UploadUIBuilder()
    comp = ui.build_file_preview_component(df, "x.csv")
    assert hasattr(comp, "children")
