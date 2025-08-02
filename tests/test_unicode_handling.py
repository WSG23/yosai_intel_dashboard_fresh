import pytest

from yosai_intel_dashboard.src.infrastructure.config.database_exceptions import UnicodeEncodingError
from yosai_intel_dashboard.src.core.unicode import UnicodeSQLProcessor


def test_surrogate_pair_encoding():
    emoji = chr(0xD83D) + chr(0xDC36)  # dog face
    result = UnicodeSQLProcessor.encode_query(emoji)
    assert result == "🐶"


def test_invalid_surrogate_handling():
    text = "bad" + chr(0xD800)
    with pytest.raises(UnicodeEncodingError) as exc_info:
        UnicodeSQLProcessor.encode_query(text)
    assert exc_info.value.original_value == text
