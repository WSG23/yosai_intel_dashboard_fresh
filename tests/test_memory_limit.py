import pandas as pd
import pytest

from tests.fake_configuration import FakeConfiguration

fake_cfg = FakeConfiguration()
from core.performance import get_performance_monitor
from yosai_intel_dashboard.src.services.data_processing.common import process_dataframe
from yosai_intel_dashboard.src.services.data_processing.file_handler import process_file_simple


def test_memory_limit_abort_csv(monkeypatch, tmp_path):
    monkeypatch.setattr(fake_cfg.performance, "memory_usage_threshold_mb", 1)
    monitor = get_performance_monitor()
    monitor.memory_threshold_mb = 1
    df = pd.DataFrame({"a": range(10)})
    path = tmp_path / "sample.csv"
    df.to_csv(path, index=False)
    content = path.read_bytes()
    with pytest.raises(MemoryError):
        process_file_simple(content, "sample.csv")


def test_memory_limit_abort_json(monkeypatch):
    monkeypatch.setattr(fake_cfg.performance, "memory_usage_threshold_mb", 1)
    monitor = get_performance_monitor()
    monitor.memory_threshold_mb = 1
    data = b'[{"a":1},{"a":2}]'
    with pytest.raises(MemoryError):
        process_dataframe(data, "sample.json")
