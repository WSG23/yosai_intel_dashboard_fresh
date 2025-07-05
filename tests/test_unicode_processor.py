import pandas as pd
from concurrent.futures import ThreadPoolExecutor

from utils.unicode_utils import safe_unicode_encode, sanitize_data_frame


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
