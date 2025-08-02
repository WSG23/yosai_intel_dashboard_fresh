import pandas as pd
import pytest

from yosai_intel_dashboard.src.core.performance_file_processor import (
    PerformanceFileProcessor as UnlimitedFileProcessor,
)
from yosai_intel_dashboard.src.core.unicode import safe_format_number, sanitize_unicode_input


@pytest.mark.performance
def test_unlimited_file_processor_handles_large_csv(tmp_path):
    df = pd.DataFrame({"A": range(200)})
    path = tmp_path / "big.csv"
    df.to_csv(path, index=False)

    proc = UnlimitedFileProcessor(chunk_size=50)
    out = proc.process_large_csv(path)

    assert len(out) == len(df)


def test_sanitize_unicode_input_strips_surrogates():
    text = "A\ud83d\ude00B"
    cleaned = sanitize_unicode_input(text)
    assert "\ud83d" not in cleaned and "\ude00" not in cleaned
    assert cleaned.startswith("A") and cleaned.endswith("B")


def test_safe_format_number_handles_special_values():
    assert safe_format_number(float("inf")) == "0"
    assert safe_format_number(float("nan")) == "0"
