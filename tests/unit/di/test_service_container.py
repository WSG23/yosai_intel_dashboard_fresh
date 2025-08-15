import pytest

from yosai_intel_dashboard.src.infrastructure.di.service_container import (
    CircularDependencyError,
    DependencyInjectionError,
    ServiceContainer,
    ServiceLifetime,
)


class B:
    pass


class A:
    def __init__(self, b: B):
        self.b = b


class X:
    def __init__(self, y: "Y"):
        self.y = y


class Y:
    def __init__(self, x: "X"):
        self.x = x


def test_singleton_and_transient():
    container = ServiceContainer()
    container.register_singleton("b", B)
    container.register_transient("a", A)

    a1 = container.get("a")
    a2 = container.get("a")
    assert a1 is not a2
    assert container.get("b") is container.get("b")


def test_circular_dependency_detection():
    c = ServiceContainer()
    c.register_transient("x", X)
    c.register_transient("y", Y)

    with pytest.raises(CircularDependencyError):
        c.get("x")
