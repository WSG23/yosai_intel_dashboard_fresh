import importlib.util
import sys
import types
from pathlib import Path

base = Path(__file__).resolve().parents[1] / "yosai_intel_dashboard/src/utils"
pkg_name = "yosai_intel_dashboard.src.utils"

# Load unicode_handler so io_helpers' relative import can resolve
uh_spec = importlib.util.spec_from_file_location(
    f"{pkg_name}.unicode_handler", base / "unicode_handler.py"
)
uh_module = importlib.util.module_from_spec(uh_spec)
uh_spec.loader.exec_module(uh_module)

# Create package module for utils
package = types.ModuleType(pkg_name)
package.__path__ = [str(base)]
sys.modules[pkg_name] = package
sys.modules[f"{pkg_name}.unicode_handler"] = uh_module

io_spec = importlib.util.spec_from_file_location(
    f"{pkg_name}.io_helpers", base / "io_helpers.py"
)
io_module = importlib.util.module_from_spec(io_spec)
io_module.__package__ = pkg_name
sys.modules[f"{pkg_name}.io_helpers"] = io_module
io_spec.loader.exec_module(io_module)
read_text = io_module.read_text
write_text = io_module.write_text


def test_io_helpers_round_trip_unpaired_surrogate(tmp_path):
    path = tmp_path / "data.txt"
    write_text(path, "A\ud83dB")
    assert path.read_text(encoding="utf-8") == "AB"
    assert read_text(path) == "AB"
