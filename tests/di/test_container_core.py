from unittest.mock import Mock

from core.container import Container


def test_container_initialization():
    container = Container()
    assert isinstance(container._services, dict)
    assert container._services == {}


def test_service_registration_and_retrieval():
    container = Container()
    service = Mock()
    container.register("svc", service)

    assert container.has("svc") is True
    assert container.get("svc") is service


def test_get_missing_service_returns_none():
    container = Container()
    assert container.get("missing") is None
    assert container.has("missing") is False
