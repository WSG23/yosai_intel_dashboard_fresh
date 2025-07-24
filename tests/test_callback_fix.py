import pytest

from core.app_factory import create_app
from core.callback_registry import _callback_registry
from core.unicode import safe_decode_bytes, safe_encode_text


def test_create_app_registers_callbacks(monkeypatch):
    monkeypatch.setattr(
        "core.app_factory.register_all_application_services", lambda *a, **k: None
    )
    monkeypatch.setattr("core.app_factory._initialize_services", lambda *a, **k: None)
    monkeypatch.setattr("core.app_factory._initialize_plugins", lambda *a, **k: None)
    app = create_app(mode="full")
    assert hasattr(app, "unified_callback")
    assert hasattr(app, "_unified_wrapper")
    assert _callback_registry.registered_callbacks
    assert _callback_registry.validate_registration_integrity()


def test_unicode_helpers():
    assert safe_encode_text("A\ud83d") == "A"
    assert safe_decode_bytes(b"hello") == "hello"
