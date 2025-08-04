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
from yosai_intel_dashboard.src.services.data_processing.file_processor import FileProcessor
from yosai_intel_dashboard.src.services.data_processing.processor import Processor
from tests.builders import TestDataBuilder
from validation.security_validator import SecurityValidator


def _create_components():
    from flask import Flask

    from yosai_intel_dashboard.src.core.cache import cache

    cache.init_app(Flask(__name__))

    fp = FileProcessor()
    vs = SecurityValidator()
    processor = Processor(validator=vs)

    ua = UploadAnalyticsProcessor(vs, processor)
    return fp, ua


def test_process_then_analyze(monkeypatch):
    fp, ua = _create_components()
    df = TestDataBuilder().add_row().build_dataframe()
    monkeypatch.setattr(ua, "load_uploaded_data", lambda: {"sample.csv": df})
    result = ua.analyze_uploaded_data()
    assert result["status"] == "success"
    assert result["rows"] == 1
