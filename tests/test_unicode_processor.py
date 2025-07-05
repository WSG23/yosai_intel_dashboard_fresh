import pandas as pd
from utils.unicode_utils import (
    safe_unicode_encode,
    sanitize_data_frame,
    UnicodeProcessor,
)


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


def test_clean_surrogate_chars_strips_control_chars():
    text = "A\x01B" + chr(0xD800) + "C\x7fD"
    cleaned = UnicodeProcessor.clean_surrogate_chars(text)
    assert cleaned == "ABCD"


def test_sanitize_data_frame_control_chars():
    df = pd.DataFrame({"a": ["x\x00\x1f", "y"]})
    cleaned = sanitize_data_frame(df)
    assert cleaned.iloc[0, 0] == "x"

