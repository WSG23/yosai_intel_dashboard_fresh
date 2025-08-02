import types

from yosai_intel_dashboard.src.core.plugins import service_locator


def test_service_locator_returns_set_plugin():
    dummy = types.SimpleNamespace(start=lambda: True)
    service_locator.set_ai_classification_plugin(dummy)
    try:
        assert service_locator.get_ai_classification_service() is dummy
    finally:
        service_locator.reset_ai_classification_plugin()


def test_service_locator_loads_via_helper(monkeypatch):
    dummy = types.SimpleNamespace(start=lambda: True)
    monkeypatch.setattr(service_locator, "_load_ai_plugin", lambda: dummy)
    service_locator.reset_ai_classification_plugin()
    assert service_locator.get_ai_classification_service() is dummy
    service_locator.reset_ai_classification_plugin()
