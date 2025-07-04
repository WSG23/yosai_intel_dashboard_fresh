import importlib
import types

import pytest

from services.registry import ServiceRegistry


def test_register_and_get_service(tmp_path, monkeypatch):
    # create dummy module
    module_dir = tmp_path / "pkg"
    module_dir.mkdir()
    mod_file = module_dir / "mod.py"
    mod_file.write_text("""\nvalue = 42\n
def func():\n    return 'hi'\n""")
    monkeypatch.syspath_prepend(str(tmp_path))

    registry = ServiceRegistry()
    registry.register_service("test", "pkg.mod:func")
    func = registry.get_service("test")
    assert callable(func)
    assert func() == "hi"

    registry.register_service("module", "pkg.mod")
    mod = registry.get_service("module")
    assert hasattr(mod, "value") and mod.value == 42


def test_get_service_missing_module(monkeypatch):
    registry = ServiceRegistry()
    registry.register_service("missing", "nope.mod:attr")

    # patch import_module to raise ImportError
    monkeypatch.setattr(importlib, "import_module", lambda name: (_ for _ in ()).throw(ImportError()))

    assert registry.get_service("missing") is None
