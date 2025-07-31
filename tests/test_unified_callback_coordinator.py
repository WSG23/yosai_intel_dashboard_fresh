import pytest
from dash import Dash, Input, Output

from yosai_intel_dashboard.src.infrastructure.callbacks.events import CallbackEvent
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks

pytestmark = pytest.mark.usefixtures("fake_dash")


def test_duplicate_callback_registration():
    app = Dash(__name__)
    coord = TrulyUnifiedCallbacks(app)

    @coord.register_callback(
        Output("out", "children"),
        Input("in", "value"),
        callback_id="dup",
        component_name="test",
    )
    def _cb(value):
        return value

    with pytest.raises(ValueError):

        @coord.register_callback(
            Output("out2", "children"),
            Input("in2", "value"),
            callback_id="dup",
            component_name="test2",
        )
        def _cb2(value):
            return value  # pragma: no cover


def test_output_conflict_detection():
    app = Dash(__name__)
    coord = TrulyUnifiedCallbacks(app)

    @coord.register_callback(
        Output("out", "children"),
        Input("a", "value"),
        callback_id="c1",
        component_name="test",
    )
    def _c1(v):
        return v

    with pytest.raises(ValueError):

        @coord.register_callback(
            Output("out", "children"),
            Input("b", "value"),
            callback_id="c2",
            component_name="test",
        )
        def _c2(v):  # pragma: no cover
            return v


def test_allow_duplicate_output():
    app = Dash(__name__)
    coord = TrulyUnifiedCallbacks(app)

    @coord.register_callback(
        Output("out", "children"),
        Input("a", "value"),
        callback_id="c1",
        component_name="test",
    )
    def _c1(v):
        return v

    # Should not raise when allow_duplicate=True
    @coord.register_callback(
        Output("out", "children"),
        Input("b", "value"),
        callback_id="c2",
        component_name="test",
        allow_duplicate=True,
    )
    def _c2(v):  # pragma: no cover
        return v


def test_allow_duplicate_on_output_obj():
    app = Dash(__name__)
    coord = TrulyUnifiedCallbacks(app)

    @coord.register_callback(
        Output("out", "children"),
        Input("x", "value"),
        callback_id="c1",
        component_name="test",
    )
    def _cb(v):
        return v

    @coord.register_callback(
        Output("out", "children", allow_duplicate=True),
        Input("y", "value"),
        callback_id="c2",
        component_name="test",
    )
    def _cb2(v):  # pragma: no cover
        return v


def test_callback_registration_to_app():
    app = Dash(__name__)
    coord = TrulyUnifiedCallbacks(app)

    @coord.register_callback(
        Output("out", "children"),
        Input("in", "value"),
        callback_id="reg",
        component_name="module",
    )
    def _cb(value):
        return value

    assert "out.children" in app.callback_map
    assert "reg" in coord.registered_callbacks


def test_get_callback_conflicts():
    app = Dash(__name__)
    coord = TrulyUnifiedCallbacks(app)

    @coord.register_callback(
        Output("out", "children"),
        Input("a", "value"),
        callback_id="c1",
        component_name="test1",
    )
    def _c1(v):
        return v

    @coord.register_callback(
        Output("out", "children"),
        Input("b", "value"),
        callback_id="c2",
        component_name="test2",
        allow_duplicate=True,
    )
    def _c2(v):
        return v

    conflicts = coord.get_callback_conflicts()
    assert conflicts["out.children"] == ["c1", "c2"]


def test_wrapper_event_registration():
    app = Dash(__name__)
    wrapper = TrulyUnifiedCallbacks(app)

    results = []

    def _event(arg):
        results.append(arg)

    wrapper.register_event(CallbackEvent.BEFORE_REQUEST, _event, priority=10)
    wrapper.trigger_event(CallbackEvent.BEFORE_REQUEST, 1)
    assert results == [1]

    @wrapper.register_callback(
        Output("o", "children"),
        Input("i", "value"),
        callback_id="cb",
        component_name="wrapper",
    )
    def _cb(v):
        return v

    assert "o.children" in app.callback_map
    assert "cb" in wrapper.registered_callbacks
