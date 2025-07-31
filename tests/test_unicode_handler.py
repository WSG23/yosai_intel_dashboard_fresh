import pytest

from yosai_intel_dashboard.src.infrastructure.config.database_exceptions import UnicodeEncodingError
from core.unicode import UnicodeSQLProcessor


def _encode_params(value):
    if isinstance(value, str):
        return UnicodeSQLProcessor.encode_query(value)
    if isinstance(value, dict):
        return {k: _encode_params(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return type(value)(_encode_params(v) for v in value)
    return value


def test_safe_encode_query_surrogates():
    text = "test" + chr(0xD800)
    with pytest.raises(UnicodeEncodingError) as exc_info:
        UnicodeSQLProcessor.encode_query(text)
    assert exc_info.value.original_value == text


def test_safe_encode_params_nested():
    params = {"a": ["b", {"c": "d" + chr(0xDCFF)}]}
    with pytest.raises(UnicodeEncodingError):
        _encode_params(params)
