import pytest
from simple_di import ServiceContainer
from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from pages.upload.callbacks import register_callbacks

pytestmark = pytest.mark.usefixtures("fake_dash")


def test_register_callbacks_uses_container(monkeypatch):
    import dash

    app = dash.Dash(__name__)
    container = ServiceContainer()

    class DummyDF:
        def to_json(self, **kwargs):
            return "dummy"

    class DummyController:
        def __init__(self):
            self.called = None

        def parse_upload(self, contents, filename):
            self.called = (contents, filename)
            return DummyDF()

    controller = DummyController()
    container.register("upload_controller", controller)

    captured = {}

    def fake_handler(self, *args, **kwargs):
        def decorator(func):
            captured["func"] = func
            return func
        return decorator

    monkeypatch.setattr(TrulyUnifiedCallbacks, "register_handler", fake_handler)

    register_callbacks(app, container)

    cb = captured["func"]
    result = cb("data", "name.csv")
    assert controller.called == ("data", "name.csv")
    assert result == (False, "dummy")
