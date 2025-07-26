from tests.fake_configuration import FakeConfiguration
import importlib.util
import sys

spec = importlib.util.spec_from_file_location(
    "services.file_processor_service", "services/file_processor_service.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
FileProcessorService = module.FileProcessorService
from core.unicode import sanitize_unicode_input


def test_decode_with_surrogate_pairs():
    svc = FileProcessorService(FakeConfiguration())
    data = "col\nval\ud83d\ude00".encode("utf-8", "surrogatepass")
    text = svc.decode_with_surrogate_handling(data, "utf-8")
    assert "val" in text
    assert "\ud83d" not in text
    assert "\ude00" not in text
