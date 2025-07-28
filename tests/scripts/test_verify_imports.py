from pathlib import Path
from scripts.verify_imports import verify_paths, main


def test_verify_paths_detects_legacy(tmp_path: Path) -> None:
    file = tmp_path / "bad.py"
    file.write_text("from yosai_intel_dashboard.src.core.domain import x\n")
    result = verify_paths([tmp_path])
    assert result == 1


def test_verify_cli_passes_when_clean(tmp_path: Path) -> None:
    file = tmp_path / "good.py"
    file.write_text(
        "from yosai_intel_dashboard.src.core.domain import x\n"

    )
    exit_code = main([str(tmp_path)])
    assert exit_code == 0

