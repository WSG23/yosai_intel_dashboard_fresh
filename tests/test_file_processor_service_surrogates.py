from tests.fake_configuration import FakeConfiguration
from services.file_processor_service import FileProcessorService
from core.unicode import sanitize_unicode_input


def test_decode_with_surrogate_pairs():
    svc = FileProcessorService(FakeConfiguration())
    data = "col\nval\ud83d\ude00".encode("utf-8", "surrogatepass")
    text = svc._decode_with_surrogate_handling(data, "utf-8")
    assert "val" in text
    assert "\ud83d" not in text
    assert "\ude00" not in text
