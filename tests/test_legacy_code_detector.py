import json
from pathlib import Path

from tools.legacy_code_detector import LegacyCodeDetector


def create_temp_file(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_detect_deprecated_imports(tmp_path):
    rules = tmp_path / "rules.yaml"
    rules.write_text("deprecated_imports:\n  - old.module\n", encoding="utf-8")

    create_temp_file(
        tmp_path / "a.py",
        "import yosai_intel_dashboard.src.services.analytics.data_loader\n",
    )
    create_temp_file(tmp_path / "b.py", "from old.module import foo\n")

    detector = LegacyCodeDetector(rules)
    report = detector.scan_directory(tmp_path)

    assert str(tmp_path / "a.py") in report
    assert str(tmp_path / "b.py") in report


def test_detect_deprecated_object(tmp_path):
    create_temp_file(tmp_path / "c.py", "from x.y import DataLoadingService\n")
    detector = LegacyCodeDetector(None)
    report = detector.scan_directory(tmp_path)
    assert str(tmp_path / "c.py") in report
    assert any(
        "DataLoadingService" in issue for issue in report[str(tmp_path / "c.py")]
    )


def test_check_requirements(tmp_path):
    rules = tmp_path / "rules.yaml"
    rules.write_text("deprecated_dependencies:\n  - obsolete\n", encoding="utf-8")
    req = tmp_path / "requirements.txt"
    req.write_text("obsolete==1.0\nflask==2.0\n", encoding="utf-8")

    detector = LegacyCodeDetector(rules)
    issues = detector.check_requirements(req)
    assert issues == ["deprecated dependency: obsolete"]
