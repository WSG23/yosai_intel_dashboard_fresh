import textwrap
from pathlib import Path
from scripts.update_imports import update_file, main


def _run_update(tmp_path: Path, content: str) -> str:
    target = tmp_path / "sample.py"
    target.write_text(textwrap.dedent(content))
    update_file(target)
    return target.read_text()


def test_update_imports_patterns(tmp_path: Path) -> None:
    before = """
    from config.utils import a
    import config.utils
    from monitoring.metrics import b
    import monitoring.metrics
    from security.auth import c
    import security.helpers
    from api.client import d
    import api.client
    from plugins.extra import e
    import plugins.extra
    """
    after = """
    from config.utils import a
    import config.utils
    from monitoring.metrics import b
    import monitoring.metrics
    from security.auth import c
    import security.helpers
    from api.client import d
    import api.client
    from api.plugins.extra import e
    import api.plugins.extra
    """
    result = _run_update(tmp_path, before)
    assert result == textwrap.dedent(after)


def test_update_imports_cli(tmp_path: Path) -> None:
    file_path = tmp_path / "example.py"
    file_path.write_text("from config import x\n")
    main([str(tmp_path)])
    expected = "from config import x\n"
    assert file_path.read_text() == expected


def test_update_imports_report_and_verify(tmp_path: Path) -> None:
    bad = tmp_path / "bad.py"
    bad.write_text("from config import y\n")
    report = tmp_path / "changes.txt"
    exit_code = main([
        str(tmp_path),
        "--verify",
        "--report",
        str(report),
    ])
    expected = "from config import y\n"
    assert bad.read_text() == expected
    assert report.read_text().strip() == str(bad)
    assert exit_code == 0

