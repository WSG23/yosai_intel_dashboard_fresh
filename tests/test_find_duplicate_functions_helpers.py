import ast

from scripts.find_duplicate_functions import _parse_python_file, _extract_functions


def test_parse_python_file_valid(tmp_path):
    file = tmp_path / "mod.py"
    file.write_text("x = 1\n")
    tree = _parse_python_file(file)
    assert isinstance(tree, ast.AST)


def test_parse_python_file_invalid(tmp_path):
    file = tmp_path / "bad.py"
    file.write_text("def bad(:\n    pass")
    assert _parse_python_file(file) is None


def test_extract_functions(tmp_path):
    code = """
from __future__ import annotations

def foo():
    return 1

class C:
    def bar(self):
        return 2
"""
    file = tmp_path / "mod.py"
    file.write_text(code)
    tree = _parse_python_file(file)
    assert tree is not None
    functions = _extract_functions(tree, file)
    names = {info.name for _, info in functions}
    assert names == {"foo", "bar"}
    bar_info = next(info for _, info in functions if info.name == "bar")
    assert bar_info.is_method
    foo_info = next(info for _, info in functions if info.name == "foo")
    assert foo_info.const_value == 1
