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
    contains_surrogates,
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
from security.unicode_security_validator import UnicodeSecurityValidator
from security.validation_exceptions import ValidationError
from config.database_exceptions import UnicodeEncodingError


def test_unicode_text_processor_surrogate_removal():
    text = "A" + chr(0xD800) + "B"
    assert UnicodeTextProcessor.clean_surrogate_chars(text) == "AB"


def test_sql_query_encoding_removes_surrogates():
    text = "SELECT" + chr(0xD800) + "1"
    with pytest.raises(UnicodeEncodingError):
        UnicodeQueryHandler.safe_encode_query(text)


def test_unicode_security_processor_sanitization():
    df = pd.DataFrame({"=bad" + chr(0xDC00): ["😀=cmd" + chr(0xD800)]})
    cleaned = UnicodeSecurityProcessor.sanitize_dataframe(df)
    assert list(cleaned.columns) == ["bad"]
    assert cleaned.iloc[0, 0] == "😀=cmd"


def test_wrapper_compatibility_and_imports():
    assert UtilsProcessor is UnicodeTextProcessor
    importlib.reload(importlib.import_module("utils.unicode_utils"))
    importlib.reload(importlib.import_module("config.unicode_handler"))
    importlib.reload(importlib.import_module("security.unicode_security_handler"))


@pytest.mark.slow
@pytest.mark.performance
def test_large_dataframe_performance():
    df = pd.DataFrame({"col": ["=bad" + chr(0xD800)] * 1_000_000})
    start = time.time()
    cleaned = sanitize_dataframe(df)
    duration = time.time() - start
    assert duration < 10
    assert cleaned.iloc[0, 0] == "bad"


def test_wrapped_contains_surrogates():
    assert contains_surrogates("x" + chr(0xD800))
    assert not contains_surrogates("emoji😀")


def test_unicode_security_validator_df():
    df = pd.DataFrame({"col": ["ok", "bad" + chr(0xD800)]})
    df_clean = UnicodeSecurityValidator.validate_dataframe(df)
    assert df_clean.iloc[1, 0] == "bad"

    valid = UnicodeSecurityValidator.validate_dataframe(pd.DataFrame({"col": ["😀ok"]}))
    assert valid.iloc[0, 0] == "😀ok"


def test_nested_values_wrapper():
    df = pd.DataFrame({"col": [["a" + chr(0xDFFF)]]})
    cleaned = sanitize_dataframe(df)
    assert cleaned.iloc[0, 0][0] == "a"
