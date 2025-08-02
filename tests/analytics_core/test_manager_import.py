import pytest

# These tests rely on the external 'analytics' package
pytest.importorskip("analytics")
from yosai_intel_dashboard.src.services.analytics.core import create_manager


def test_create_manager() -> None:
    manager = create_manager()
    assert manager.core_service
    assert manager.ai_service
