import sys
from core.plugins.manager import ThreadSafePluginManager as PluginManager
from core.container import Container as DIContainer
import types


class DummyConfigManager:
    def __init__(self):
        self.config = types.SimpleNamespace(plugin_settings={})

    def get_plugin_config(self, name: str):
        return self.config.plugin_settings.get(name, {})


def _create_cycle_pkg(tmp_path):
    pkg_dir = tmp_path / "cyclepkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "a.py").write_text(
        """
from services.data_processing.core.protocols import PluginMetadata

class APlugin:
    metadata = PluginMetadata(
        name='a',
        version='0.1',
        description='a',
        author='t',
        dependencies=['b']
    )
    def load(self, c, cfg):
        return True
    def configure(self, cfg):
        return True
    def start(self):
        return True
    def stop(self):
        return True
    def health_check(self):
        return {'healthy': True}

def create_plugin():
    return APlugin()
"""
    )
    (pkg_dir / "b.py").write_text(
        """
from services.data_processing.core.protocols import PluginMetadata

class BPlugin:
    metadata = PluginMetadata(
        name='b',
        version='0.1',
        description='b',
        author='t',
        dependencies=['a']
    )
    def load(self, c, cfg):
        return True
    def configure(self, cfg):
        return True
    def start(self):
        return True
    def stop(self):
        return True
    def health_check(self):
        return {'healthy': True}

def create_plugin():
    return BPlugin()
"""
    )
    return pkg_dir


def _create_missing_dep_pkg(tmp_path):
    pkg_dir = tmp_path / "misspkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "plug.py").write_text(
        """
from services.data_processing.core.protocols import PluginMetadata

class P:
    metadata = PluginMetadata(
        name='a',
        version='0.1',
        description='a',
        author='t',
        dependencies=['missing']
    )
    def load(self, c, cfg):
        return True
    def configure(self, cfg):
        return True
    def start(self):
        return True
    def stop(self):
        return True
    def health_check(self):
        return {'healthy': True}

def create_plugin():
    return P()
"""
    )
    return pkg_dir


def _set_required_env(monkeypatch):
    envs = {
        "SECRET_KEY": "x",
        "DB_PASSWORD": "x",
        "AUTH0_CLIENT_ID": "x",
        "AUTH0_CLIENT_SECRET": "x",
        "AUTH0_DOMAIN": "x",
        "AUTH0_AUDIENCE": "x",
    }
    for k, v in envs.items():
        monkeypatch.setenv(k, v)


def test_cycle_logging(caplog, monkeypatch):
    _set_required_env(monkeypatch)
    cfg = DummyConfigManager()
    mgr = PluginManager(DIContainer(), cfg, health_check_interval=1)

    def fail(_):
        raise ValueError("Circular dependency detected: a -> b -> a")

    monkeypatch.setattr(mgr._resolver, "resolve", fail)

    with caplog.at_level('ERROR', logger='core.plugins.manager'):
        result = mgr.load_all_plugins()

    assert result == []
    assert any('Plugin dependency cycle detected' in r.getMessage() for r in caplog.records)
    mgr.stop_health_monitor()


def test_unknown_dep_logging(caplog, monkeypatch):
    _set_required_env(monkeypatch)
    cfg = DummyConfigManager()
    mgr = PluginManager(DIContainer(), cfg, health_check_interval=1)

    def fail(_):
        raise ValueError("Unknown dependencies: x")

    monkeypatch.setattr(mgr._resolver, "resolve", fail)

    with caplog.at_level('ERROR', logger='core.plugins.manager'):
        result = mgr.load_all_plugins()

    assert result == []
    assert any('Unknown dependencies' in r.getMessage() for r in caplog.records)
    mgr.stop_health_monitor()
