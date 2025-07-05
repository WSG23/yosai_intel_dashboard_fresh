import importlib
import time
import pandas as pd
import pytest
import warnings

from core.unicode_processor import UnicodeProcessor as UnicodeTextProcessor
from core.unicode import (
    clean_unicode_text,
    safe_encode_text,
    sanitize_dataframe,
    UnicodeProcessor as UtilsProcessor,
    # Test deprecated functions
    safe_unicode_encode,
    safe_encode,
    safe_decode,
    handle_surrogate_characters,
    clean_unicode_surrogates,
    sanitize_unicode_input,
    sanitize_data_frame,
)
from config.unicode_handler import UnicodeQueryHandler
from security.unicode_security_handler import UnicodeSecurityHandler as UnicodeSecurityProcessor


def test_unicode_text_processor_surrogate_removal():
    text = "A" + chr(0xD800) + "B"
    assert UnicodeTextProcessor.clean_surrogate_chars(text) == "AB"


def test_sql_query_encoding_removes_surrogates():
    text = "SELECT" + chr(0xD800) + "1"
    encoded = UnicodeQueryHandler.safe_encode_query(text)
    assert "SELECT" in encoded and "1" in encoded
    assert "\ud800" not in encoded


def test_unicode_security_processor_sanitization():
    df = pd.DataFrame({"=bad" + chr(0xDC00): ["=cmd" + chr(0xD800)]})
    cleaned = UnicodeSecurityProcessor.sanitize_dataframe(df)
    assert list(cleaned.columns) == ["bad"]
    assert cleaned.iloc[0, 0] == "cmd"


def test_wrapper_compatibility_and_imports():
    assert UtilsProcessor is UnicodeTextProcessor
    importlib.reload(importlib.import_module("utils.unicode_utils"))
    importlib.reload(importlib.import_module("config.unicode_handler"))
    importlib.reload(importlib.import_module("security.unicode_security_handler"))


@pytest.mark.slow
def test_large_dataframe_performance():
    df = pd.DataFrame({"col": ["=bad" + chr(0xD800)] * 1_000_000})
    start = time.time()
    cleaned = sanitize_dataframe(df)
    duration = time.time() - start
    assert duration < 10
    assert cleaned.iloc[0, 0] == "bad"
