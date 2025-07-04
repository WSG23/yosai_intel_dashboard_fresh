import pytest

from core.enhanced_container import ServiceContainer


def test_singleton_registration_and_retrieval():
    container = ServiceContainer()
    obj = object()
    container.register_singleton("obj", obj)
    assert container.get("obj") is obj
    assert container.has("obj")


def test_factory_registration_and_caching():
    container = ServiceContainer()
    calls = []

    def factory():
        calls.append(1)
        return {"value": len(calls)}

    container.register_factory("svc", factory)

    first = container.get("svc")
    second = container.get("svc")
    assert first == second
    assert calls == [1]


def test_missing_service_raises():
    container = ServiceContainer()
    with pytest.raises(ValueError):
        container.get("missing")
