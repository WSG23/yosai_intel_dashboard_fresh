import sys
import types

import pytest

from security_callback_controller import SecurityEvent


@pytest.fixture
def capture_events(monkeypatch: pytest.MonkeyPatch, validator_module) -> list:
    """Capture security events emitted by the validator."""

    events: list = []
    monkeypatch.setattr(
        validator_module,
        "emit_security_event",
        lambda event, data=None: events.append(event),
    )
    return events


@pytest.fixture(autouse=True)
def fake_flask(monkeypatch: pytest.MonkeyPatch):
    """Provide minimal Flask stub for importing security modules."""

    flask_stub = types.ModuleType("flask")

    class _Flask:
        def __init__(self, *args, **kwargs):
            pass

    flask_stub.Flask = _Flask
    monkeypatch.setitem(sys.modules, "flask", flask_stub)
    yield flask_stub


@pytest.fixture
def validator_module(fake_flask):
    """Import the validator module with dependencies stubbed."""

    import importlib

    sys.modules.pop("core.unicode", None)
    importlib.import_module("core.unicode")
    return importlib.import_module("security.unicode_surrogate_validator")


def test_contains_surrogates_detects(validator_module):
    assert validator_module.contains_surrogates("a\ud800b")
    assert not validator_module.contains_surrogates("abc")
    # Valid surrogate pair should not be flagged
    assert not validator_module.contains_surrogates("\ud800\udc00")


def test_remove_mode(capture_events, validator_module):
    validator = validator_module.UnicodeSurrogateValidator()
    result = validator.sanitize("A\ud800B")
    assert result == "AB"
    assert capture_events and capture_events[0] == SecurityEvent.VALIDATION_FAILED


def test_replace_mode(validator_module):
    cfg = validator_module.SurrogateHandlingConfig(mode="replace", replacement="?")
    validator = validator_module.UnicodeSurrogateValidator(cfg)
    assert validator.sanitize("x\ud800y") == "x?y"


def test_strict_mode(validator_module):
    cfg = validator_module.SurrogateHandlingConfig(mode="strict")
    validator = validator_module.UnicodeSurrogateValidator(cfg)
    with pytest.raises(Exception):
        validator.sanitize("bad\ud800")
