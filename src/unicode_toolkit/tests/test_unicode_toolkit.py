import sys
import types
import pytest

try:
    import pandas as pd
    if not hasattr(pd, "DataFrame"):
        pd = None
except Exception:  # pragma: no cover - pandas not available
    pd = None
    pandas_stub = types.ModuleType("pandas")
    pandas_stub.isna = lambda x: x is None
    sys.modules["pandas"] = pandas_stub

db_exc_stub = types.ModuleType(
    "yosai_intel_dashboard.src.infrastructure.config.database_exceptions"
)

class UnicodeEncodingError(Exception):
    def __init__(self, message: str, original_value: str) -> None:
        super().__init__(message)
        self.original_value = original_value


db_exc_stub.UnicodeEncodingError = UnicodeEncodingError
sys.modules.setdefault(
    "yosai_intel_dashboard.src.infrastructure.config.database_exceptions",
    db_exc_stub,
)

from unicode_toolkit import sanitize_input
from yosai_intel_dashboard.src.core.unicode import (
    UnicodeProcessor,
    UnicodeSQLProcessor,
    sanitize_dataframe,
)
from yosai_intel_dashboard.src.core.exceptions import SecurityError


def test_processor_basic():
    assert UnicodeProcessor.clean_text("A\ud800B") == "AB"
    assert UnicodeProcessor.clean_surrogate_chars("X\ud800Y") == "XY"


@pytest.mark.skipif(pd is None, reason="pandas not available")
def test_dataframe_helper():
    df = pd.DataFrame({"=c\ud800": ["val\udfff"]})
    with pytest.raises(SecurityError):
        sanitize_dataframe(df)


def test_sql_encoding():
    assert UnicodeSQLProcessor.encode_query("SELECT 'a'") == "SELECT 'a'"


def test_surrogate_pair_removed():
    assert UnicodeProcessor.clean_text("\uD83D\uDE00") == "😀"


def test_special_characters_preserved():
    text = "Café ☕"
    assert UnicodeProcessor.clean_text(text) == text


def test_sanitize_input_special_chars():
    raw = "<b>hi & bye</b>"
    assert sanitize_input(raw) == "&lt;b&gt;hi &amp; bye&lt;&#x2F;b&gt;"
