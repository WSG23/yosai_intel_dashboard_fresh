import types

import pytest

from core.plugins.dependency_resolver import PluginDependencyResolver


class FakePlugin:
    def __init__(self, name, deps=None):
        self.metadata = types.SimpleNamespace(name=name, dependencies=deps)


def test_resolver_orders_by_dependencies():
    a = FakePlugin("a", ["b"])
    b = FakePlugin("b", ["c"])
    c = FakePlugin("c")
    resolver = PluginDependencyResolver()

    ordered = resolver.resolve([a, c, b])
    names = [p.metadata.name for p in ordered]
    assert names == ["c", "b", "a"]


def test_resolver_detects_cycles():
    a = FakePlugin("a", ["b"])
    b = FakePlugin("b", ["a"])
    resolver = PluginDependencyResolver()

    with pytest.raises(ValueError):
        resolver.resolve([a, b])
