import dash
from dash import Input, Output

from core.unified_callback_coordinator import UnifiedCallbackCoordinator
from core.callback_registry import CallbackRegistry
from core.plugins.decorators import unified_callback


def test_unified_decorator_with_coordinator():
    app = dash.Dash(__name__)
    coord = UnifiedCallbackCoordinator(app)

    @unified_callback(
        coord,
        Output("out", "children"),
        Input("in", "value"),
        callback_id="uc1",
        component_name="test",
    )
    def _cb(v):
        return v

    assert "out.children" in app.callback_map
    assert "uc1" in coord.registered_callbacks


def test_unified_decorator_method():
    app = dash.Dash(__name__)
    coord = UnifiedCallbackCoordinator(app)

    @coord.unified_callback(
        Output("o", "children"),
        Input("i", "value"),
        callback_id="uc2",
        component_name="test",
    )
    def _cb2(v):
        return v

    assert "o.children" in app.callback_map
    assert "uc2" in coord.registered_callbacks


def test_unified_with_registry():
    app = dash.Dash(__name__)
    registry = CallbackRegistry(app)

    @unified_callback(
        registry,
        Output("r", "children"),
        Input("x", "value"),
        callback_id="uc3",
        component_name="reg",
    )
    def _cb3(v):
        return v

    assert "r.children" in app.callback_map
    assert "uc3" in registry.registered_callbacks
