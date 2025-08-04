import importlib
import sys
import types


def load_module(monkeypatch):
    module_name = "yosai_intel_dashboard.src.infrastructure.di"
    settings = types.SimpleNamespace(
        get_database_config=lambda: {"db": 1},
        get_analytics_config=lambda: {"ana": 2},
    )
    fake_config = types.SimpleNamespace(get_config=lambda: settings)
    monkeypatch.setitem(
        sys.modules, "yosai_intel_dashboard.src.infrastructure.config", fake_config
    )
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def test_builtin_config_lookups(monkeypatch):
    di = load_module(monkeypatch)
    assert di.container.get("config").get_database_config() == {"db": 1}
    assert di.container.get("database_config") == {"db": 1}
    assert di.container.get("analytics_config") == {"ana": 2}


def test_register_and_helpers(monkeypatch):
    di = load_module(monkeypatch)
    di.register_singleton("foo", 42)
    assert di.container.get("foo") == 42

    di.register_factory("bar", lambda c: {"n": 1})
    assert di.container.get("bar") == {"n": 1}

    di.configure_database(lambda c: "dbsvc")
    di.configure_analytics(lambda c: "anasvc")
    assert di.container.get("database_service") == "dbsvc"
    assert di.container.get("analytics_service") == "anasvc"
