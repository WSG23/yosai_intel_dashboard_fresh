import pandas as pd
from concurrent.futures import ThreadPoolExecutor

import time
import pytest

from utils.unicode_utils import (
    safe_unicode_encode,
    sanitize_data_frame,
    safe_decode,
    safe_encode,
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
    text = "Ａ" + "\x00" + chr(0xD800) + "B" + "\u212B"
    result = safe_unicode_encode(text)
    # fullwidth A and Angstrom sign should normalize, control char and surrogate removed
    assert result == "ABA"


def test_dataframe_sanitization_edge_cases():
    df = pd.DataFrame({"=bad\x00": ["=cmd" + chr(0xD800), "\x07\u212B"]})
    cleaned = sanitize_data_frame(df)
    assert list(cleaned.columns) == ["bad"]
    assert cleaned.iloc[0, 0] == "cmd"
    assert cleaned.iloc[1, 0] == "A"


def test_safe_decode_encode_no_errors():
    data = ("X" + chr(0xD800) + "Y").encode("utf-8", "surrogatepass")
    decoded = safe_decode(data)
    encoded = safe_encode(decoded + chr(0xDFFF))
    assert isinstance(decoded, str) and isinstance(encoded, str)
    assert "\ud800" not in decoded and "\udfff" not in encoded


@pytest.mark.slow
def test_sanitize_dataframe_benchmark():
    df = pd.DataFrame({"=col": ["=1"] * 100})
    start = time.time()
    for _ in range(100):
        sanitize_data_frame(df)
    assert time.time() - start < 5

