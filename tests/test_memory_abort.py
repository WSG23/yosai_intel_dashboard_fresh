import pandas as pd
import pytest

from yosai_intel_dashboard.src.core.performance_file_processor import PerformanceFileProcessor


class FakeProcess:
    def __init__(self, rss_values):
        self._rss = rss_values
        self.calls = 0

    def memory_info(self):
        class Mem:
            def __init__(self, rss):
                self.rss = rss

        rss = self._rss[min(self.calls, len(self._rss) - 1)]
        self.calls += 1
        return Mem(rss)


def test_abort_on_memory_limit(monkeypatch, tmp_path):
    df = pd.DataFrame({"a": range(10)})
    path = tmp_path / "data.csv"
    df.to_csv(path, index=False)

    fake_proc = FakeProcess([10 * 1024 * 1024, 200 * 1024 * 1024])
    monkeypatch.setattr(
        "core.performance_file_processor.psutil.Process", lambda: fake_proc
    )

    processor = PerformanceFileProcessor(chunk_size=5, max_memory_mb=50)
    with pytest.raises(MemoryError):
        processor.process_large_csv(path)
