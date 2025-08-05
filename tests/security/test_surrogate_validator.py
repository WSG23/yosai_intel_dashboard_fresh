import pytest

from yosai_intel_dashboard.src.infrastructure.security import (
    events as security_callback_controller,
)
from yosai_intel_dashboard.src.infrastructure.security.events import SecurityEvent


@pytest.fixture
def capture_events(monkeypatch: pytest.MonkeyPatch, validator_module) -> list:
    """Capture security events emitted by the validator."""

    events: list = []
    monkeypatch.setattr(
        security_callback_controller,
        "emit_security_event",
        lambda event, data=None: events.append(event),
    )
    return events


@pytest.fixture
def validator_module():
    """Import the validator module fresh for each test."""

    import importlib

    from yosai_intel_dashboard.src.infrastructure.security import (
        unicode_surrogate_validator as mod,
    )

    importlib.reload(mod)
    # Provide SecurityEvent for the lazy import pattern used in the module
    mod.SecurityEvent = SecurityEvent
    return mod


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


def test_init_allows_valid_replacement(validator_module):
    cfg = validator_module.SurrogateHandlingConfig(mode="replace", replacement="!")
    validator = validator_module.UnicodeSurrogateValidator(cfg)
    assert validator.config.replacement == "!"


def test_init_rejects_surrogate_replacement(validator_module):
    cfg = validator_module.SurrogateHandlingConfig(mode="replace", replacement="\ud800")
    with pytest.raises(ValueError):
        validator_module.UnicodeSurrogateValidator(cfg)
