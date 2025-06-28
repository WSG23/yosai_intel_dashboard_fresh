import pytest
from dash import Dash, Input, Output

from core.unified_callback_coordinator import UnifiedCallbackCoordinator


def test_duplicate_callback_registration():
    app = Dash(__name__)
    coord = UnifiedCallbackCoordinator(app)

    @coord.register_callback(Output('out', 'children'), Input('in', 'value'),
                             callback_id='dup', component_name='test')
    def _cb(value):
        return value

    with pytest.raises(ValueError):
        @coord.register_callback(Output('out2', 'children'), Input('in2', 'value'),
                                 callback_id='dup', component_name='test2')
        def _cb2(value):
            return value  # pragma: no cover


def test_output_conflict_detection():
    app = Dash(__name__)
    coord = UnifiedCallbackCoordinator(app)

    @coord.register_callback(Output('out', 'children'), Input('a', 'value'),
                             callback_id='c1', component_name='test')
    def _c1(v):
        return v

    with pytest.raises(ValueError):
        @coord.register_callback(Output('out', 'children'), Input('b', 'value'),
                                 callback_id='c2', component_name='test')
        def _c2(v):  # pragma: no cover
            return v


def test_allow_duplicate_output():
    app = Dash(__name__)
    coord = UnifiedCallbackCoordinator(app)

    @coord.register_callback(Output('out', 'children'), Input('a', 'value'),
                             callback_id='c1', component_name='test')
    def _c1(v):
        return v

    # Should not raise when allow_duplicate=True
    @coord.register_callback(
        Output('out', 'children'),
        Input('b', 'value'),
        callback_id='c2',
        component_name='test',
        allow_duplicate=True
    )
    def _c2(v):  # pragma: no cover
        return v


def test_allow_duplicate_on_output_obj():
    app = Dash(__name__)
    coord = UnifiedCallbackCoordinator(app)

    @coord.register_callback(Output('out', 'children'), Input('x', 'value'),
                             callback_id='c1', component_name='test')
    def _cb(v):
        return v

    @coord.register_callback(
        Output('out', 'children', allow_duplicate=True),
        Input('y', 'value'),
        callback_id='c2',
        component_name='test'
    )
    def _cb2(v):  # pragma: no cover
        return v


def test_callback_registration_to_app():
    app = Dash(__name__)
    coord = UnifiedCallbackCoordinator(app)

    @coord.register_callback(Output('out', 'children'), Input('in', 'value'),
                             callback_id='reg', component_name='module')
    def _cb(value):
        return value

    assert 'out.children' in app.callback_map
    assert 'reg' in coord.registered_callbacks

