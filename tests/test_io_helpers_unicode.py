import json
import importlib.util
import sys
import types
from pathlib import Path

# Create minimal package structure
sys.modules.setdefault(
    "yosai_intel_dashboard", types.ModuleType("yosai_intel_dashboard")
)
sys.modules.setdefault(
    "yosai_intel_dashboard.src", types.ModuleType("yosai_intel_dashboard.src")
)
sys.modules.setdefault(
    "yosai_intel_dashboard.src.utils",
    types.ModuleType("yosai_intel_dashboard.src.utils"),
)

# Stub unicode_toolkit.safe_encode_text
unicode_toolkit_stub = types.ModuleType("unicode_toolkit")


def safe_encode_text(value):
    if isinstance(value, bytes):
        value = value.decode("utf-8", "ignore")
    return value.encode("utf-8", "surrogatepass").decode("utf-8", "ignore")


unicode_toolkit_stub.safe_encode_text = safe_encode_text
sys.modules["unicode_toolkit"] = unicode_toolkit_stub

# Stub UnicodeHandler
uh_stub = types.ModuleType("yosai_intel_dashboard.src.utils.unicode_handler")


class StubUnicodeHandler:
    @staticmethod
    def sanitize(obj):
        if isinstance(obj, str):
            return safe_encode_text(obj)
        if isinstance(obj, dict):
            return {k: StubUnicodeHandler.sanitize(v) for k, v in obj.items()}
        return obj


uh_stub.UnicodeHandler = StubUnicodeHandler
sys.modules["yosai_intel_dashboard.src.utils.unicode_handler"] = uh_stub

# Load io_helpers module
spec = importlib.util.spec_from_file_location(
    "yosai_intel_dashboard.src.utils.io_helpers",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard/src/utils/io_helpers.py",
)
io_helpers = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = io_helpers
spec.loader.exec_module(io_helpers)

read_text = io_helpers.read_text
write_text = io_helpers.write_text
read_json = io_helpers.read_json
write_json = io_helpers.write_json


def test_write_and_read_text_handles_surrogates(tmp_path):
    content = "A\ud83dB"
    path = tmp_path / "file.txt"
    write_text(path, content)
    assert path.read_text(encoding="utf-8") == "AB"
    assert read_text(path) == "AB"


def test_write_and_read_json_handles_surrogates(tmp_path):
    data = {"t": "A\ud83dB"}
    path = tmp_path / "data.json"
    write_json(path, data)
    assert json.loads(path.read_text(encoding="utf-8")) == {"t": "AB"}
    assert read_json(path) == {"t": "AB"}
