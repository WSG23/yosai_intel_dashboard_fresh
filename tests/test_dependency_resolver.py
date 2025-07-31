from __future__ import annotations

import sys

import pytest

from config import create_config_manager
from core.plugins.dependency_resolver import PluginDependencyResolver
from core.plugins.manager import PluginManager
from core.protocols.plugin import PluginMetadata
from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer


class DummyPlugin:
    def __init__(self, name, deps=None):
        self.metadata = PluginMetadata(
            name=name,
            version="0.1",
            description=name,
            author="tester",
            dependencies=deps,
        )

    def load(self, container, config):
        return True

    def configure(self, config):
        return True

    def start(self):
        return True

    def stop(self):
        return True

    def health_check(self):
        return {"healthy": True}


def test_resolver_orders_dependencies():
    a = DummyPlugin("a")
    b = DummyPlugin("b", ["a"])
    c = DummyPlugin("c", ["b"])
    resolver = PluginDependencyResolver()
    ordered = resolver.resolve([c, b, a])
    assert [p.metadata.name for p in ordered][:3] == ["a", "b", "c"]


def test_resolver_unknown_dependency():
    p = DummyPlugin("a", ["missing"])
    resolver = PluginDependencyResolver()
    with pytest.raises(ValueError, match="Unknown dependencies"):  # noqa: PT011
        resolver.resolve([p])


def test_resolver_cycle_detection():
    a = DummyPlugin("a", ["b"])
    b = DummyPlugin("b", ["a"])
    resolver = PluginDependencyResolver()
    with pytest.raises(ValueError, match="Circular dependency"):  # noqa: PT011
        resolver.resolve([a, b])


def _create_pkg(tmp_path, name):
    pkg_dir = tmp_path / name
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    return pkg_dir


def test_manager_cycle_logging(tmp_path, caplog, mock_auth_env):
    pkg = _create_pkg(tmp_path, "cyclepkg")
    (pkg / "plug_a.py").write_text(
        """
from core.protocols.plugin import PluginMetadata

class PlugA:
    metadata = PluginMetadata(
        name='plug_a',
        version='0.1',
        description='a',
        author='tester',
        dependencies=['plug_b'],
    )
    def load(self, c, conf):
        return True
    def configure(self, conf):
        return True
    def start(self):
        return True
    def stop(self):
        return True
    def health_check(self):
        return {'healthy': True}

def create_plugin():
    return PlugA()
"""
    )
    (pkg / "plug_b.py").write_text(
        """
from core.protocols.plugin import PluginMetadata

class PlugB:
    metadata = PluginMetadata(
        name='plug_b',
        version='0.1',
        description='b',
        author='tester',
        dependencies=['plug_a'],
    )
    def load(self, c, conf):
        return True
    def configure(self, conf):
        return True
    def start(self):
        return True
    def stop(self):
        return True
    def health_check(self):
        return {'healthy': True}

def create_plugin():
    return PlugB()
"""
    )
    sys.path.insert(0, str(tmp_path))
    manager = PluginManager(
        ServiceContainer(),
        create_config_manager(),
        package="cyclepkg",
        health_check_interval=1,
    )
    try:
        caplog.set_level("ERROR")
        result = manager.load_all_plugins()
        assert result == []
        assert any(
            "Plugin dependency cycle detected" in r.getMessage() for r in caplog.records
        )
    finally:
        sys.path.remove(str(tmp_path))
        manager.stop_health_monitor()


def test_manager_unknown_dependency_logging(tmp_path, caplog, mock_auth_env):
    pkg = _create_pkg(tmp_path, "unkpkg")
    (pkg / "plug_a.py").write_text(
        """
from core.protocols.plugin import PluginMetadata

class PlugA:
    metadata = PluginMetadata(
        name='plug_a',
        version='0.1',
        description='a',
        author='tester',
        dependencies=['missing'],
    )
    def load(self, c, conf):
        return True
    def configure(self, conf):
        return True
    def start(self):
        return True
    def stop(self):
        return True
    def health_check(self):
        return {'healthy': True}

def create_plugin():
    return PlugA()
"""
    )
    sys.path.insert(0, str(tmp_path))
    manager = PluginManager(
        ServiceContainer(),
        create_config_manager(),
        package="unkpkg",
        health_check_interval=1,
    )
    try:
        caplog.set_level("ERROR")
        result = manager.load_all_plugins()
        assert result == []
        assert any(
            "Failed to resolve plugin dependencies" in r.getMessage()
            for r in caplog.records
        )
    finally:
        sys.path.remove(str(tmp_path))
        manager.stop_health_monitor()
