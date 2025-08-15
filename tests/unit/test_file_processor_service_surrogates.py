import importlib.util
import sys

from tests.config import FakeConfiguration
from yosai_intel_dashboard.src.core.imports.resolver import safe_import

spec = importlib.util.spec_from_file_location(
    "services.file_processor_service", "services/file_processor_service.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
FileProcessorService = module.FileProcessorService
from yosai_intel_dashboard.src.core.unicode import sanitize_unicode_input


def test_decode_with_surrogate_pairs():
    svc = FileProcessorService(FakeConfiguration())
    data = "col\nval\ud83d\ude00".encode("utf-8", "surrogatepass")
    text = svc.decode_with_surrogate_handling(data, "utf-8")
    assert "val" in text
    assert "\ud83d" not in text
    assert "\ude00" not in text
