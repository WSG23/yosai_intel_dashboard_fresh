import pytest

from core.app_factory import create_app
from core.callback_registry import _callback_registry
from core.unicode import safe_encode_text, safe_decode_bytes


def test_app_factory_and_registry():
    app = create_app()
    assert hasattr(app, "unified_callback")
    assert hasattr(app, "_unified_wrapper")

    # registry should have callbacks registered
    assert _callback_registry.registered_callbacks
    assert _callback_registry.validate_registration_integrity()


def test_unicode_helpers():
    assert safe_encode_text("hello") == "hello"
    assert safe_decode_bytes(b"world") == "world"
