import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "unicode_handler_module",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard/src/utils/unicode_handler.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
UnicodeHandler = module.UnicodeHandler
safe_encode_text = module.safe_encode_text


def test_unicode_handler_sanitizes_unpaired_surrogate():
    assert UnicodeHandler.sanitize("A\ud83dB") == "AB"


def test_unicode_handler_sanitizes_nested_structures():
    data = {"k": "A\ud83dB", "l": ["x\ud83dy"]}
    expected = {"k": "AB", "l": ["xy"]}
    assert UnicodeHandler.sanitize(data) == expected


def test_module_safe_encode_text_matches_handler():
    assert safe_encode_text("A\ud83dB") == "AB"
