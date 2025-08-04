import pandas as pd

import importlib.util
import sys
import types
from pathlib import Path

base = Path(__file__).resolve().parents[1] / "yosai_intel_dashboard/src/services/upload"
pkg_name = "yosai_intel_dashboard.src.services.upload"
if pkg_name not in sys.modules:
    pkg = types.ModuleType("upload")
    pkg.__path__ = [str(base)]
    sys.modules[pkg_name] = pkg

spec_proto = importlib.util.spec_from_file_location(
    f"{pkg_name}.protocols", base / "protocols.py"
)
protocols = importlib.util.module_from_spec(spec_proto)
spec_proto.loader.exec_module(protocols)
sys.modules[f"{pkg_name}.protocols"] = protocols

spec = importlib.util.spec_from_file_location(
    f"{pkg_name}.upload_processing", base / "upload_processing.py"
)
upload_processing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload_processing)
UploadAnalyticsProcessor = upload_processing.UploadAnalyticsProcessor
from yosai_intel_dashboard.src.services.data_processing.processor import Processor
from tests.utils.builders import DataFrameBuilder
from validation.security_validator import SecurityValidator


def _make_processor():
    from flask import Flask

    from yosai_intel_dashboard.src.core.cache import cache

    cache.init_app(Flask(__name__))
    vs = SecurityValidator()
    processor = Processor(validator=vs)
    return UploadAnalyticsProcessor(vs, processor)


def test_load_data_helper(monkeypatch):
    df = DataFrameBuilder().add_column("A", [1]).build()
    ua = _make_processor()
    monkeypatch.setattr(ua, "load_uploaded_data", lambda: {"f.csv": df})
    assert ua._load_data() == {"f.csv": df}


def test_validate_data_filters_empty():
    df = DataFrameBuilder().add_column("A", [1]).build()
    ua = _make_processor()
    data = {"empty.csv": pd.DataFrame(), "f.csv": df}
    cleaned = ua._validate_data(data)
    assert list(cleaned.keys()) == ["f.csv"]


def test_calculate_statistics():
    df = (
        DataFrameBuilder()
        .add_column("Person ID", ["u1"])
        .add_column("Device name", ["d1"])
        .build()
    )
    ua = _make_processor()
    stats = ua._calculate_statistics({"x.csv": df})
    assert stats["rows"] == 1
    assert stats["columns"] == 2


def test_format_results():
    ua = _make_processor()
    formatted = ua._format_results({"rows": 1})
    assert formatted["status"] == "success"
    assert formatted["rows"] == 1
