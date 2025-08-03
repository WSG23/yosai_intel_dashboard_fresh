from __future__ import annotations

from pathlib import Path

from tools.check_execute_query import find_violations


def test_detects_direct_call(tmp_path):
    code = (
        "from database.secure_exec import execute_query\n"
        "def bad(factory):\n"
        "    execute_query(factory.get_connection(), 'SELECT 1')\n"
    )
    file = tmp_path / "bad.py"
    file.write_text(code)
    issues = find_violations([file])
    assert file in issues and issues[file]


def test_repository_has_no_direct_calls():
    issues = find_violations([Path.cwd()])
    assert issues == {}
