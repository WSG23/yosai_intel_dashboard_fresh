import pytest
from dash import Dash
from dash.dependencies import Input, Output

from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks

pytestmark = pytest.mark.usefixtures("fake_dash")


def test_tuc_class():
    assert issubclass(TrulyUnifiedCallbacks, TrulyUnifiedCallbacks)


def test_basic_dash_registration():
    app = Dash(__name__)
    system = TrulyUnifiedCallbacks(app)

    @system.register_dash_callback(
        Output("o", "children"),
        Input("i", "value"),
        callback_id="cb",
        component_name="test",
    )
    def _cb(v):
        return v

    assert "o.children" in app.callback_map
