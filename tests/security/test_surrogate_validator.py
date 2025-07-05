import importlib.util
import sys
import types

import pytest

spec = importlib.util.spec_from_file_location(
    "security.unicode_surrogate_validator",
    "security/unicode_surrogate_validator.py",
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

UnicodeSurrogateValidator = module.UnicodeSurrogateValidator
SurrogateHandlingConfig = module.SurrogateHandlingConfig
contains_surrogates = module.contains_surrogates
from security_callback_controller import SecurityEvent


def test_contains_surrogates_detects():
    assert contains_surrogates("a\ud800b")
    assert not contains_surrogates("abc")


def test_remove_mode(monkeypatch):
    events = []
    monkeypatch.setattr(
        module,
        "emit_security_event",
        lambda event, data=None: events.append(event),
    )
    validator = UnicodeSurrogateValidator()
    result = validator.sanitize("A\ud800B")
    assert result == "AB"
    assert events and events[0] == SecurityEvent.VALIDATION_FAILED


def test_replace_mode():
    cfg = SurrogateHandlingConfig(mode="replace", replacement="?")
    validator = UnicodeSurrogateValidator(cfg)
    assert validator.sanitize("x\ud800y") == "x?y"


def test_strict_mode():
    cfg = SurrogateHandlingConfig(mode="strict")
    validator = UnicodeSurrogateValidator(cfg)
    with pytest.raises(Exception):
        validator.sanitize("bad\ud800")
