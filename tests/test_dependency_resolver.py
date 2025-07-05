import pytest

from core.plugins.dependency_resolver import PluginDependencyResolver
from services.data_processing.core.protocols import PluginMetadata


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
