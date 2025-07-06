import json
from pathlib import Path

import pytest

from models.css_build_optimizer import (
    PathValidationError,
    ensure_output_directory,
    generate_css_report_safe,
    safe_path_conversion,
    validate_css_directory,
)


def test_validate_css_directory_success(tmp_path):
    result = validate_css_directory(tmp_path)
    assert isinstance(result, Path)


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


def test_generate_css_report_safe(tmp_path):
    css_dir = tmp_path / "css"
    css_dir.mkdir()
    (css_dir / "main.css").write_text("body {color: #000;}\n")
    output = tmp_path / "report.json"

    report = generate_css_report_safe(str(css_dir), output)

    assert output.exists()
    loaded = json.loads(output.read_text())
    assert loaded["overall_score"] == report["overall_score"]
