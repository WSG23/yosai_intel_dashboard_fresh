import pytest

pytestmark = pytest.mark.usefixtures("fake_dash")


def test_register_callbacks(fake_dash, monkeypatch):
    import tests.stubs.dash.html as html_stub
    for tag in ["H1", "H4", "P", "Hr"]:
        setattr(html_stub, tag, html_stub.Div)

    import tests.stubs.dash_bootstrap_components as dbc_stub
    class DummyDiv(dbc_stub._Base):
        pass
    dbc_stub.Progress = DummyDiv
    import tests.stubs.dash.dcc as dcc_stub
    dcc_stub.Upload = DummyDiv

    import types, sys
    fake_app = types.ModuleType("services.data_enhancer.app")

    class EnhancedFileProcessor:
        @staticmethod
        def decode_contents(*a, **k):
            return None, ""

    class MultiBuildingDataEnhancer:
        STANDARD_FIELDS = []

        @staticmethod
        def get_enhanced_column_suggestions(*a, **k):
            return {}

        @staticmethod
        def get_enhanced_device_suggestions(*a, **k):
            return {}

        @staticmethod
        def apply_column_mappings(df, mapping):
            return df

        @staticmethod
        def apply_device_mappings(df, mapping):
            return df

        @staticmethod
        def _detect_building_type(s):
            return ""

        @staticmethod
        def _detect_floor_advanced(s):
            return 0

        @staticmethod
        def _generate_building_name(t, s):
            return ""

    fake_app.EnhancedFileProcessor = EnhancedFileProcessor
    fake_app.MultiBuildingDataEnhancer = MultiBuildingDataEnhancer
    def create_standalone_app():
        class DummyApp:
            pass
        return DummyApp()
    fake_app.create_standalone_app = create_standalone_app
    sys.modules["services.data_enhancer.app"] = fake_app

    cli_stub = types.ModuleType("services.data_enhancer.cli")
    cli_stub.run_data_enhancer = lambda: None
    cli_stub.create_standalone_app = create_standalone_app
    sys.modules["services.data_enhancer.cli"] = cli_stub

    fake_dash.callback_context = types.SimpleNamespace(triggered=[])
    fake_dash.dash_table = types.SimpleNamespace(DataTable=DummyDiv)

    import dash
    app = dash.Dash(__name__)
    captured = []

    class DummyCoord:
        def __init__(self, app):
            self.app = app

        def callback(self, *args, **kwargs):
            def decorator(func):
                captured.append(func)
                return func

            return decorator

    monkeypatch.setattr(
        "services.data_enhancer.callbacks.TrulyUnifiedCallbacks", DummyCoord
    )

    from services.data_enhancer.callbacks import register_callbacks

    register_callbacks(app, None)

    assert captured, "Callbacks were not registered"
