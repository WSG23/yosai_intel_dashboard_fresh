import importlib.util
import json
from pathlib import Path

from scripts.scan_try_except import find_redundant_trys

spec = importlib.util.spec_from_file_location(
    "reporting", Path("yosai_intel_dashboard/src/infrastructure/security/reporting.py")
)
reporting = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(reporting)
load_result = reporting.load_result


def test_load_result_and_missing(tmp_path: Path) -> None:
    data = {"name": "sample", "severity": "LOW"}
    file = tmp_path / "result.json"
    file.write_text(json.dumps(data), encoding="utf-8")
    assert load_result(file) == data
    assert load_result(tmp_path / "missing.json") is None


def test_find_redundant_trys_detects(tmp_path: Path) -> None:
    pyfile = tmp_path / "sample.py"
    pyfile.write_text(
        "def foo():\n    try:\n        pass\n    except Exception:\n        pass\n",
        encoding="utf-8",
    )
    results = find_redundant_trys(tmp_path)
    assert pyfile in results
    assert results[pyfile]
