import pytest
from dash import Dash
from dash.dependencies import Input, Output

from core.master_callback_system import MasterCallbackSystem
from core.truly_unified_callbacks import TrulyUnifiedCallbacks

pytestmark = pytest.mark.usefixtures("fake_dash")


def test_mcs_is_wrapper():
    assert issubclass(MasterCallbackSystem, TrulyUnifiedCallbacks)


def test_basic_dash_registration():
    app = Dash(__name__)
    system = MasterCallbackSystem(app)

    @system.register_dash_callback(
        Output("o", "children"),
        Input("i", "value"),
        callback_id="cb",
        component_name="test",
    )
    def _cb(v):
        return v

    assert "o.children" in app.callback_map
