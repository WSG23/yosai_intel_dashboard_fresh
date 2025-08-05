from __future__ import annotations

import pandas as pd
import sys
from types import ModuleType, SimpleNamespace
from pathlib import Path

sys.modules[
    "yosai_intel_dashboard.src.utils.hashing"
] = SimpleNamespace(hash_dataframe=lambda df: "")
analytics_dir = Path(__file__).resolve().parents[1] / "yosai_intel_dashboard/src/services/analytics"
analytics_pkg = ModuleType("yosai_intel_dashboard.src.services.analytics")
analytics_pkg.__path__ = [str(analytics_dir)]
sys.modules["yosai_intel_dashboard.src.services.analytics"] = analytics_pkg

from tests.infrastructure import uploaded_data
from tests.utils.builders import DataFrameBuilder
from validation.security_validator import SecurityValidator
from yosai_intel_dashboard.src.services.analytics.upload_analytics import (
    UploadAnalyticsProcessor,
)
from yosai_intel_dashboard.src.services.data_processing.processor import Processor


@pytest.fixture(scope="module")
def factory() -> MockFactory:
    with TestInfrastructure(MockFactory(), stub_packages=[]) as f:
        stubs_path = Path(infra_mod.__file__).resolve().parents[1] / "stubs"
        if str(stubs_path) in sys.path:
            sys.path.remove(str(stubs_path))
        yield f


def test_load_data_helper(factory: MockFactory, monkeypatch):
    df = factory.dataframe({"A": [1]})
    ua = factory.upload_processor()
    monkeypatch.setattr(ua, "load_uploaded_data", lambda: {"f.csv": df})
    assert ua._load_data() == {"f.csv": df}


def test_validate_data_filters_empty():
    valid_df = DataFrameBuilder().add_column("A", [1]).build()
    ua = _make_processor()
    data = uploaded_data(("empty.csv", pd.DataFrame()), ("valid.csv", valid_df))

    cleaned = ua._validate_data(data)
    assert list(cleaned.keys()) == ["valid.csv"]


def test_calculate_statistics(factory: MockFactory):
    df = factory.dataframe({"Person ID": ["u1"], "Device name": ["d1"]})
    ua = factory.upload_processor()
    stats = ua._calculate_statistics({"x.csv": df})
    assert stats["rows"] == 1
    assert stats["columns"] == 2


def test_format_results(factory: MockFactory):
    ua = factory.upload_processor()
    formatted = ua._format_results({"rows": 1})
    assert formatted["status"] == "success"
    assert formatted["rows"] == 1
