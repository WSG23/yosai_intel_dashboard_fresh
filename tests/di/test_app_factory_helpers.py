import importlib
from types import SimpleNamespace

from core.service_container import ServiceContainer
from core.protocols import UnicodeProcessorProtocol
from core.app_factory.plugins import _initialize_plugins
from core.app_factory import (
    _setup_layout,
    _register_callbacks,
    _configure_swagger,
)
from tests.fake_configuration import FakeConfiguration


class DummyServer:
    def __init__(self) -> None:
        self.teardown_funcs = []
        self.config = {}

    def teardown_appcontext(self, func):
        self.teardown_funcs.append(func)
        return func


class DummyApp:
    def __init__(self) -> None:
        self.server = DummyServer()


def _make_container(proc: UnicodeProcessorProtocol) -> ServiceContainer:
    container = ServiceContainer()
    container.register_singleton("config_manager", FakeConfiguration)
    container.register_singleton(
        "unicode_processor", lambda: proc, protocol=UnicodeProcessorProtocol
    )
    return container


def test_initialize_plugins(fake_unicode_processor):
    app = DummyApp()
    container = _make_container(fake_unicode_processor)
    cfg = container.get("config_manager")

    auto_instances = []

    class DummyPM:
        def stop_all_plugins(self):
            self.stopped = True

        def stop_health_monitor(self):
            self.monitor_stopped = True

    class DummyAuto:
        def __init__(self, *a, **k):
            auto_instances.append(self)
            self.registry = SimpleNamespace(plugin_manager=DummyPM())
            self.scanned = None
            self.generated = False

        def scan_and_configure(self, pkg):
            self.scanned = pkg

        def generate_health_endpoints(self):
            self.generated = True

    _initialize_plugins(
        app,
        cfg,
        container=container,
        plugin_auto_cls=DummyAuto,
    )

    auto = auto_instances[0]
    assert auto.scanned == "plugins"
    assert auto.generated is True
    assert hasattr(app, "_yosai_plugin_manager")
    assert isinstance(app._yosai_plugin_manager, DummyPM)
    assert app.server.teardown_funcs


def test_setup_layout(monkeypatch):
    app = DummyApp()
    monkeypatch.setattr(
        importlib.import_module("core.app_factory"),
        "_create_main_layout",
        lambda: "layout1",
    )
    _setup_layout(app)
    assert app.layout() == "layout1"
    monkeypatch.setattr(
        importlib.import_module("core.app_factory"),
        "_create_main_layout",
        lambda: "layout2",
    )
    assert app.layout() == "layout1"


def test_register_callbacks(monkeypatch, fake_unicode_processor):
    app = DummyApp()
    container = _make_container(fake_unicode_processor)
    cfg = container.get("config_manager")

    # Ensure stub modules are used for callback registration
    import sys
    from pathlib import Path

    stub_dir = Path(__file__).resolve().parents[1] / "stubs"
    if str(stub_dir) not in sys.path:
        sys.path.insert(0, str(stub_dir))
    for mod in [
        "pages",
        "pages.file_upload",
        "pages.deep_analytics",
        "components.simple_device_mapping",
        "components.device_verification",
        "components.ui.navbar",
    ]:
        sys.modules.pop(mod, None)
    import tests.stubs.dash_bootstrap_components as dbc_stub

    sys.modules["dash_bootstrap_components"] = dbc_stub

    calls = {}

    def fake_global(mgr):
        calls["global"] = True

    monkeypatch.setattr(
        importlib.import_module("core.app_factory"),
        "_register_global_callbacks",
        fake_global,
    )

    instance = None

    class DummyCoord:
        def __init__(self, app):
            nonlocal instance
            instance = self
            self.app = app
            self.summary = False

        def unified_callback(self, *a, **k):  # pragma: no cover - simple stub
            def decorator(func):
                return func

            return decorator

        register_callback = unified_callback

        def print_callback_summary(self):
            self.summary = True

    monkeypatch.setattr(
        importlib.import_module("core.app_factory"), "TrulyUnifiedCallbacks", DummyCoord
    )

    _register_callbacks(app, cfg, container=container)

    assert calls["global"]
    assert getattr(instance, "simple_registered", False)
    assert getattr(instance, "device_registered", False)
    assert getattr(instance, "deep_registered", False)
    assert getattr(instance, "upload_registered", False)
    assert getattr(instance, "navbar_registered", False)
    assert hasattr(app, "_upload_callbacks")
    assert hasattr(app, "_deep_analytics_callbacks")


def test_configure_swagger(monkeypatch):
    server = DummyServer()
    captured = {}

    class DummySwagger:
        def __init__(self, srv, template=None):
            captured["template"] = template
            srv.swagger = True

    monkeypatch.setattr(
        importlib.import_module("core.app_factory"), "Swagger", DummySwagger
    )
    _configure_swagger(server)
    assert server.config["SWAGGER"]["uiversion"] == 3
    assert captured["template"]["info"]["title"] == "Yōsai Intel Dashboard API"
    assert hasattr(server, "swagger")
