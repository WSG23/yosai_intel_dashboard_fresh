import pytest
from dash import Dash, Input, Output

from core.plugins.decorators import handle_safe, safe_callback
from core.truly_unified_callbacks import TrulyUnifiedCallbacks


def test_imports():
    assert handle_safe is safe_callback


def test_plugin_style():
    @handle_safe()
    def cb():
        return "works"

    assert cb() == "works"


def test_factory_style_registration():
    app = Dash(__name__)
    manager = TrulyUnifiedCallbacks(app)

    @handle_safe(
        Output("o", "children"),
        Input("i", "value"),
        callback_id="test_cb",
        manager=manager,
        component_name="test",
    )
    def cb2(value=None):
        return value

    assert "test_cb" in manager.registered_callbacks


def test_manager_usage():
    app = Dash(__name__)
    manager = TrulyUnifiedCallbacks(app)
    assert manager.app is app
