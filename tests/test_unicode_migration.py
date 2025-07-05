import pandas as pd
import pytest

from core.unicode import (
    UnicodeProcessor,
    ChunkedUnicodeProcessor,
    clean_unicode_text,
    safe_decode_bytes,
    safe_encode_text,
    sanitize_dataframe,
    # Deprecated functions for testing
    safe_unicode_encode,
    safe_encode,
    safe_decode,
    handle_surrogate_characters,
    clean_unicode_surrogates,
    sanitize_unicode_input,
    sanitize_data_frame,
)


def test_surrogate_removal():
    text = "Hello\uD83D\uDE00World"
    assert clean_unicode_text(text) == "HelloWorld"


def test_control_character_removal():
    assert UnicodeProcessor.clean_text("A\x01B\x7fC") == "ABC"


def test_csv_injection_prevention():
    assert safe_encode_text("=cmd()") == "cmd()"


def test_dataframe_sanitization():
    df = pd.DataFrame({"col\uD83D": ["val\uDE00"]})
    clean_df = sanitize_dataframe(df)
    assert list(clean_df.columns) == ["col"]
    assert clean_df.iloc[0, 0] == "val"


def test_chunked_processing():
    content = ("Hello\uD83D\uDE00World" * 500).encode("utf-8", "surrogatepass")
    result = ChunkedUnicodeProcessor.process_large_content(content, chunk_size=128)
    assert result == "HelloWorld" * 500


def test_deprecated_functions_issue_warnings():
    with pytest.warns(DeprecationWarning):
        assert safe_unicode_encode("test\uD83D") == "test"
    with pytest.warns(DeprecationWarning):
        assert safe_encode("test\uD83D") == "test"
    data = ("X\uD83D").encode("utf-8", "surrogatepass")
    with pytest.warns(DeprecationWarning):
        assert safe_decode(data).startswith("X")
    with pytest.warns(DeprecationWarning):
        assert handle_surrogate_characters("A\uD83DB") == "A\uFFFDB"
    with pytest.warns(DeprecationWarning):
        assert clean_unicode_surrogates("A\uD83DB") == "AB"
    with pytest.warns(DeprecationWarning):
        assert sanitize_unicode_input("A\uD83D") == "A"
    df = pd.DataFrame({"=bad\uD83D": ["=cmd()"]})
    with pytest.warns(DeprecationWarning):
        legacy = sanitize_data_frame(df)
    modern = sanitize_dataframe(df)
    pd.testing.assert_frame_equal(legacy, modern)


def test_error_handling_invalid_bytes():
    bad = b"\xff\xfe\xfa"
    out = safe_decode_bytes(bad)
    assert isinstance(out, str)

