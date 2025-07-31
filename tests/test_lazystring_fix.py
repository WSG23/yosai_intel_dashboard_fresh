import pytest

from yosai_intel_dashboard.src.infrastructure.config.constants import SecurityLimits
from core.serialization import SafeJSONSerializer

serializer = SafeJSONSerializer()


def _contains_surrogate(text: str) -> bool:
    return any(0xD800 <= ord(ch) <= 0xDFFF for ch in text)


def test_surrogate_pair_removed():
    text = "\ud800\udc00test"
    result = serializer.serialize(text)
    assert result == "\ud800\udc00test"


def test_lone_surrogate_removed():
    text = "start\ud800end"
    result = serializer.serialize(text)
    assert not _contains_surrogate(result)


def test_unicode_normalization():
    # Angstrom sign -> Latin capital A with ring above
    text = "\u212b"
    result = serializer.serialize(text)
    assert result == "\u00c5"


def test_nested_structures_and_types():
    try:
        from flask_babel import lazy_gettext
    except Exception:
        pytest.skip("flask_babel not available")

    data = {
        "msg": lazy_gettext("hello"),
        "items": [1, lazy_gettext("bye"), {"again": lazy_gettext("again")}],
    }
    sanitized = serializer.serialize(data)
    assert sanitized["msg"] == "hello"
    assert sanitized["items"][1] == "bye"
    assert sanitized["items"][2]["again"] == "again"
    assert sanitized["items"][0] == 1


@pytest.mark.performance
def test_long_string_performance():
    text = "a" * SecurityLimits.MAX_INPUT_STRING_LENGTH_CHARACTERS
    result = serializer.serialize(text)
    assert result == text
