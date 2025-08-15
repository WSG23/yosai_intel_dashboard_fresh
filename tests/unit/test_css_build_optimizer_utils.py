import importlib
import json
import sys
import types
from pathlib import Path

import pytest


@pytest.fixture
def css_build_optimizer(stub_services_registry):
    """Import ``css_build_optimizer`` with a stubbed registry."""

    module = importlib.import_module("models.css_build_optimizer")
    return importlib.reload(module)


def test_validate_css_directory_success(tmp_path, css_build_optimizer):
    result = css_build_optimizer.validate_css_directory(tmp_path)
    assert result == tmp_path
    assert result.exists() and result.is_dir()


def test_validate_css_directory_failure(tmp_path, css_build_optimizer):
    missing = tmp_path / "missing"
    with pytest.raises(css_build_optimizer.PathValidationError):
        css_build_optimizer.validate_css_directory(missing)


def test_ensure_output_directory_creates_parent(tmp_path, css_build_optimizer):
    target = tmp_path / "sub" / "report.json"
    result = css_build_optimizer.ensure_output_directory(target)
    assert result == target
    assert target.parent.exists()


def test_safe_path_conversion(tmp_path, css_build_optimizer):
    p = tmp_path / "file.txt"
    assert css_build_optimizer.safe_path_conversion(p) == str(p)
    assert css_build_optimizer.safe_path_conversion(str(p)) == str(p)

    class BadPath:
        def __init__(self):
            self.called = False

        def __str__(self):
            if not self.called:
                self.called = True
                raise ValueError("boom")
            return "bad"

    with pytest.raises(css_build_optimizer.PathValidationError):
        css_build_optimizer.safe_path_conversion(BadPath())

    windows_path = Path("C:\\path\\to\\file.txt")
    assert css_build_optimizer.safe_path_conversion(windows_path) == str(windows_path)


def test_generate_css_report_safe(tmp_path, css_build_optimizer):
    css_dir = tmp_path / "css"
    css_dir.mkdir()
    (css_dir / "main.css").write_text("body {color: #000;}\n")
    output = tmp_path / "report.json"

    report = css_build_optimizer.generate_css_report_safe(str(css_dir), output)

    assert output.exists()
    loaded = json.loads(output.read_text())
    assert loaded["overall_score"] == report["overall_score"]
