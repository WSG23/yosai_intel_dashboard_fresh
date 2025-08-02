from unittest.mock import Mock

import pytest

from yosai_intel_dashboard.src.core.container import Container
from yosai_intel_dashboard.src.infrastructure.di.service_container import DependencyInjectionError


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


def test_get_missing_service_raises_error():
    container = Container()
    with pytest.raises(DependencyInjectionError):
        container.get("missing")
    assert container.has("missing") is False
