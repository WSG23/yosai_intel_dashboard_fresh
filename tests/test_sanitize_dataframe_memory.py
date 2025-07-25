import pandas as pd
import psutil
import pytest

from yosai_intel_dashboard.src.services.data_processing.file_processor import UnicodeFileProcessor


@pytest.mark.slow
@pytest.mark.performance
def test_sanitize_dataframe_unicode_memory_usage():
    rows = 10_000
    df = pd.DataFrame({"text": ["bad\ud83d\ude00"] * rows})

    proc = UnicodeFileProcessor()
    process = psutil.Process()
    start_mem = process.memory_info().rss / (1024 * 1024)
    total = 0
    for chunk in proc.sanitize_dataframe_unicode(df, chunk_size=5_000, stream=True):
        assert not chunk["text"].str.contains("\\ud83d").any()
        total += len(chunk)
    end_mem = process.memory_info().rss / (1024 * 1024)
    assert total == rows
    assert end_mem - start_mem < 100
