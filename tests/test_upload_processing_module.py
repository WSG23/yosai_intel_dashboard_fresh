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


def test_direct_processing_helper(tmp_path):
    df1 = (
        DataFrameBuilder()
        .add_column("Timestamp", ["2024-01-01 10:00:00"])
        .add_column("Person ID", ["u1"])
        .add_column("Token ID", ["t1"])
        .add_column("Device name", ["d1"])
        .add_column("Access result", ["Granted"])
        .build()
    )
    proc = _make_processor()
    result = proc._process_uploaded_data_directly({"f1.csv": df1})
    assert result["rows"] == 1
    assert result["columns"] == 5
