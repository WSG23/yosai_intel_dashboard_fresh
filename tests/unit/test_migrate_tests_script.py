import textwrap
from pathlib import Path

from scripts import migrate_tests


def test_replace_sys_modules_setdefault():
    lines = ["sys.modules.setdefault('pkg', object())"]
    new_lines, todos = migrate_tests.replace_sys_modules(lines)
    assert new_lines == ["safe_import('pkg', object())"]
    assert todos == []


def test_process_file_rewrites(tmp_path: Path):
    source = textwrap.dedent(
        """
        import sys

        sys.modules['pkg'] = object()
        """
    ).strip()
    path = tmp_path / "sample.py"
    path.write_text(source)

    todos = migrate_tests.process_file(path)

    rewritten = path.read_text().splitlines()
    assert "from tests.import_helpers import safe_import, import_optional" in rewritten
    assert "safe_import('pkg', object())" in rewritten
    assert todos == []
