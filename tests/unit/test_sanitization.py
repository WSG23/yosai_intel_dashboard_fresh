import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location(
    "sanitization",
    Path("yosai_intel_dashboard/src/utils/sanitization.py"),
)
san = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(san)


def test_script_tags_removed():
    dirty = "<script>alert('x')</script>hello"
    assert san.sanitize_text(dirty) == "alert('x')hello"


def test_sanitize_filename_blocks_traversal():
    assert san.sanitize_filename("safe.csv") == "safe.csv"
    with pytest.raises(ValueError):
        san.sanitize_filename("../bad.csv")
