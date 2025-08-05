from __future__ import annotations

import pandas as pd
import pytest
import sys
from pathlib import Path
import tests.infrastructure as infra_mod

from tests.infrastructure import MockFactory, TestInfrastructure


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


def test_validate_data_filters_empty(factory: MockFactory):
    df = factory.dataframe({"A": [1]})
    ua = factory.upload_processor()
    data = {"empty.csv": pd.DataFrame(), "f.csv": df}
    cleaned = ua._validate_data(data)
    assert list(cleaned.keys()) == ["f.csv"]


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
