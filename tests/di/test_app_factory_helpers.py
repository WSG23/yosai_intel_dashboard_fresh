import importlib.util
import sys
from types import ModuleType, SimpleNamespace
from pathlib import Path

# Ensure stub modules are importable before loading the factory
ROOT = Path(__file__).resolve().parents[2]
STUB_DIR = ROOT / "tests" / "stubs"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(STUB_DIR))


spec = importlib.util.spec_from_file_location("core.app_factory", ROOT / "core" / "app_factory.py")
app_factory = importlib.util.module_from_spec(spec)
sys.modules["core.app_factory"] = app_factory
comp_pkg = ModuleType("components")
comp_pkg.__path__ = []
sys.modules.setdefault("components", comp_pkg)
ui_pkg = ModuleType("components.ui")
ui_pkg.__path__ = []
sys.modules.setdefault("components.ui", ui_pkg)
sys.modules.setdefault("components.ui.navbar", ModuleType("components.ui.navbar"))
sys.modules["components.ui.navbar"].create_navbar_layout = lambda: "navbar"
sys.modules.setdefault("core.unicode_processor", ModuleType("core.unicode_processor"))
sys.modules["core.unicode_processor"].safe_format_number = lambda *a, **k: ""
sys.modules.setdefault("core.unicode", ModuleType("core.unicode"))
config_pkg = ModuleType("config")
config_pkg.__path__ = []
sys.modules.setdefault("config", config_pkg)
sys.modules.setdefault("config.config", ModuleType("config.config"))
sys.modules["config.config"].get_config = lambda: SimpleNamespace(get_app_config=lambda: SimpleNamespace(environment="development"), get_analytics_config=lambda: SimpleNamespace(title="title"))
core_pkg = ModuleType("core")
core_pkg.__path__ = []
sys.modules.setdefault("core", core_pkg)
sys.modules.setdefault("core.container", ModuleType("core.container"))
sys.modules["core.container"].Container = object
sys.modules.setdefault("core.enhanced_container", ModuleType("core.enhanced_container"))
sys.modules["core.enhanced_container"].ServiceContainer = object
sys.modules.setdefault("core.plugins.auto_config", ModuleType("core.plugins.auto_config"))
sys.modules["core.plugins.auto_config"].PluginAutoConfiguration = lambda *a, **k: None
sys.modules.setdefault("core.secrets_manager", ModuleType("core.secrets_manager"))
sys.modules["core.secrets_manager"].validate_secrets = lambda: {}
sys.modules.setdefault("core.theme_manager", ModuleType("core.theme_manager"))
sys.modules["core.theme_manager"].DEFAULT_THEME = "light"
sys.modules["core.theme_manager"].apply_theme_settings = lambda app: None
sys.modules["core.theme_manager"].sanitize_theme = lambda x: x
sys.modules.setdefault("dash_csrf_plugin", ModuleType("dash_csrf_plugin"))
sys.modules["dash_csrf_plugin"].CSRFMode = SimpleNamespace(PRODUCTION="prod")
sys.modules["dash_csrf_plugin"].setup_enhanced_csrf_protection = lambda *a, **k: None
sys.modules.setdefault("services", ModuleType("services"))
sys.modules["services"].get_analytics_service = lambda: SimpleNamespace(health_check=lambda: "ok")
sys.modules.setdefault("core.cache", ModuleType("core.cache"))
sys.modules["core.cache"].cache = SimpleNamespace(init_app=lambda x: None)
spec.loader.exec_module(app_factory)  # type: ignore

class DummyServer:
    def __init__(self):
        self.teardown_funcs = []
        self.config = {}
    def teardown_appcontext(self, func):
        self.teardown_funcs.append(func)
        return func

class DummyApp:
    def __init__(self):
        self.server = DummyServer()


def test_initialize_plugins(monkeypatch):
    app = DummyApp()

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

    monkeypatch.setattr(app_factory, "PluginAutoConfiguration", DummyAuto)
    app_factory._initialize_plugins(app, object())

    auto = auto_instances[0]
    assert auto.scanned == "plugins"
    assert auto.generated is True
    assert hasattr(app, "_yosai_plugin_manager")
    assert isinstance(app._yosai_plugin_manager, DummyPM)
    assert app.server.teardown_funcs


def test_setup_layout(monkeypatch):
    app = DummyApp()
    monkeypatch.setattr(app_factory, "_create_main_layout", lambda: "layout1")
    app_factory._setup_layout(app)
    assert app.layout() == "layout1"
    monkeypatch.setattr(app_factory, "_create_main_layout", lambda: "layout2")
    assert app.layout() == "layout1"


def test_register_callbacks(monkeypatch):
    app = DummyApp()
    cfg = SimpleNamespace(get_app_config=lambda: SimpleNamespace(environment="development"))

    calls = {}
    def fake_router(mgr):
        calls["router"] = True
    def fake_global(mgr):
        calls["global"] = True
    monkeypatch.setattr(app_factory, "_register_router_callbacks", fake_router)
    monkeypatch.setattr(app_factory, "_register_global_callbacks", fake_global)

    class DummyCoord:
        def __init__(self, app):
            self.app = app
            self.summary = False
        def print_callback_summary(self):
            self.summary = True
    monkeypatch.setattr(app_factory, "TrulyUnifiedCallbacks", DummyCoord)

    # stub modules for component registrations
    sys.modules["components.device_verification"] = SimpleNamespace(register_callbacks=lambda m: calls.setdefault("device", True))
    sys.modules["components.simple_device_mapping"] = SimpleNamespace(register_callbacks=lambda m: calls.setdefault("simple", True))
    sys.modules["components.ui.navbar"] = SimpleNamespace(
        register_navbar_callbacks=lambda m, svc=None: calls.setdefault("nav", True)
    )
    sys.modules["pages.deep_analytics.callbacks"] = SimpleNamespace(
        Callbacks=type("CB1", (), {}),
        register_callbacks=lambda m: calls.setdefault("deep", True),
    )
    sys.modules["pages.file_upload"] = SimpleNamespace(
        Callbacks=type("CB2", (), {}),
        register_callbacks=lambda m: calls.setdefault("upload", True),
    )

    app_factory._register_callbacks(app, cfg)

    assert calls["router"] and calls["global"]
    assert calls["device"] and calls["simple"] and calls["nav"]
    assert calls["deep"] and calls["upload"]
    assert hasattr(app, "_upload_callbacks")
    assert hasattr(app, "_deep_analytics_callbacks")


def test_configure_swagger(monkeypatch):
    server = DummyServer()
    captured = {}
    class DummySwagger:
        def __init__(self, srv, template=None):
            captured["template"] = template
            srv.swagger = True
    monkeypatch.setattr(app_factory, "Swagger", DummySwagger)
    app_factory._configure_swagger(server)
    assert server.config["SWAGGER"]["uiversion"] == 3
    assert captured["template"]["info"]["title"] == "Yōsai Intel Dashboard API"
    assert hasattr(server, "swagger")
