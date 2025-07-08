import json
import importlib.util
import sys
import types
from pathlib import Path

import pytest

# Avoid heavy service imports when loading the module under test
services_mod = types.ModuleType("services")
registry_mod = types.ModuleType("services.registry")
registry_mod.get_service = lambda name: None
services_mod.registry = registry_mod
sys.modules.setdefault("services", services_mod)
sys.modules.setdefault("services.registry", registry_mod)

spec = importlib.util.spec_from_file_location(
    "css_build_optimizer",
    Path(__file__).resolve().parents[1] / "models" / "css_build_optimizer.py",
)
css_build_optimizer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(css_build_optimizer)

PathValidationError = css_build_optimizer.PathValidationError
ensure_output_directory = css_build_optimizer.ensure_output_directory
generate_css_report_safe = css_build_optimizer.generate_css_report_safe
safe_path_conversion = css_build_optimizer.safe_path_conversion
validate_css_directory = css_build_optimizer.validate_css_directory


def test_validate_css_directory_success(tmp_path):
    result = validate_css_directory(tmp_path)
    assert result == tmp_path
    assert result.exists() and result.is_dir()


def test_validate_css_directory_failure(tmp_path):
    missing = tmp_path / "missing"
    with pytest.raises(PathValidationError):
        validate_css_directory(missing)


def test_ensure_output_directory_creates_parent(tmp_path):
    target = tmp_path / "sub" / "report.json"
    result = ensure_output_directory(target)
    assert result == target
    assert target.parent.exists()


def test_safe_path_conversion(tmp_path):
    p = tmp_path / "file.txt"
    assert safe_path_conversion(p) == str(p)
    assert safe_path_conversion(str(p)) == str(p)

    class BadPath:
        def __init__(self):
            self.called = False

        def __str__(self):
            if not self.called:
                self.called = True
                raise ValueError("boom")
            return "bad"

    with pytest.raises(PathValidationError):
        safe_path_conversion(BadPath())

    windows_path = Path("C:\\path\\to\\file.txt")
    assert safe_path_conversion(windows_path) == str(windows_path)


def test_generate_css_report_safe(tmp_path):
    css_dir = tmp_path / "css"
    css_dir.mkdir()
    (css_dir / "main.css").write_text("body {color: #000;}\n")
    output = tmp_path / "report.json"

    report = generate_css_report_safe(str(css_dir), output)

    assert output.exists()
    loaded = json.loads(output.read_text())
    assert loaded["overall_score"] == report["overall_score"]
