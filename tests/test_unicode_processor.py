import pandas as pd
import pytest
import time
from concurrent.futures import ThreadPoolExecutor

from core.unicode_processor import (
    safe_unicode_encode,
    sanitize_data_frame,
    safe_format_number,
    safe_decode,
    safe_encode,
    contains_surrogates,
)
from security.unicode_security_validator import UnicodeSecurityValidator
from security.validation_exceptions import ValidationError



def test_safe_unicode_encode_surrogates():
    text = "A" + chr(0xD800) + "B"
    assert safe_unicode_encode(text) == "AB"

    encoded = ("X" + chr(0xDC00) + "Y").encode("utf-8", "surrogatepass")
    assert safe_unicode_encode(encoded) == "XY"


def test_sanitize_data_frame():
    df = pd.DataFrame({"=bad" + chr(0xDC00): ["=cmd()", "ok" + chr(0xD800)]})
    cleaned = sanitize_data_frame(df)
    assert list(cleaned.columns) == ["bad"]
    assert cleaned.iloc[0, 0] == "cmd()"
    assert cleaned.iloc[1, 0] == "ok"


def test_unicode_processor_thread_safety():
    df = pd.DataFrame({"=bad": ["=cmd()" + chr(0xD800), "ok"]})

    expected = sanitize_data_frame(df)

    def worker(_: int) -> pd.DataFrame:
        return sanitize_data_frame(df)

    with ThreadPoolExecutor(max_workers=5) as exc:
        results = list(exc.map(worker, range(10)))

    for result in results:
        pd.testing.assert_frame_equal(result, expected)



def test_clean_surrogate_control_nfkc():
    text = "Ａ" + "😀" + "\x00" + chr(0xD800) + "B" + "\u212B"
    result = safe_unicode_encode(text)
    # emoji should survive, others cleaned
    assert result == "A😀BÅ"


def test_dataframe_sanitization_edge_cases():
    df = pd.DataFrame({"=bad\x00": ["=cmd" + chr(0xD800), "\x07\u212B"]})
    cleaned = sanitize_data_frame(df)
    assert list(cleaned.columns) == ["bad"]
    assert cleaned.iloc[0, 0] == "cmd"
    assert cleaned.iloc[1, 0] == "Å"


def test_safe_decode_encode_no_errors():
    data = ("X" + chr(0xD800) + "Y").encode("utf-8", "surrogatepass")
    decoded = safe_decode(data)
    encoded = safe_encode(decoded + chr(0xDFFF))
    assert isinstance(decoded, str) and isinstance(encoded, str)
    assert "\ud800" not in decoded and "\udfff" not in encoded


def test_safe_format_number_handles_special_values():
    assert safe_format_number(float("nan")) is None
    assert safe_format_number(float("inf")) is None
    assert safe_format_number(12345) == "12,345"


def test_contains_surrogates_helper():
    assert contains_surrogates("test" + chr(0xD800))
    assert not contains_surrogates("ok😀")


def test_unicode_security_validator():
    validator = UnicodeSecurityValidator()
    assert validator.validate_text("bad" + chr(0xDFFF)) == "bad"
    assert validator.validate_text("good😀") == "good😀"


def test_dataframe_nested_values_cleaned():
    df = pd.DataFrame({"col": [{"a": "ok" + chr(0xD800)}]})
    cleaned = sanitize_data_frame(df)
    assert cleaned.iloc[0, 0]["a"] == "ok"


@pytest.mark.slow
def test_sanitize_dataframe_benchmark():
    df = pd.DataFrame({"=col": ["=1"] * 100})
    start = time.time()
    for _ in range(100):
        sanitize_data_frame(df)
    assert time.time() - start < 5

