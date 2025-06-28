import pytest
from dash import Dash, Input, Output, html

from core.callback_manager import CallbackManager


def test_duplicate_callback_registration():
    app = Dash(__name__)
    manager = CallbackManager(app)

    @manager.callback(Output('out', 'children'), Input('in', 'value'), callback_id='dup')
    def _cb(value):
        return value

    with pytest.raises(ValueError):
        @manager.callback(Output('out2', 'children'), Input('in2', 'value'), callback_id='dup')
        def _cb2(value):  # pragma: no cover - should not run
            return value


def test_callback_registration_to_app():
    app = Dash(__name__)
    manager = CallbackManager(app)

    @manager.callback(Output('out', 'children'), Input('in', 'value'), callback_id='reg')
    def _cb(value):
        return value

    assert 'out.children' in app.callback_map
    assert 'reg' in manager.registered_ids
