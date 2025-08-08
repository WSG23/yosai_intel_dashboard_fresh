from __future__ import annotations

import importlib
import logging
import sys

import pytest

import optional_dependencies


@pytest.mark.parametrize("name", ["concurrent.futures", "cryptography.fernet"])
def test_import_optional_submodule_without_warning(name, caplog):
    orig_mod = sys.modules.pop(name, None)
    orig_fallback = optional_dependencies._fallbacks.pop(name, None)
    try:
        if importlib.util.find_spec(name) is None:
            pytest.skip(f"{name} not available")
        base = name.rsplit(".", 1)[0]
        importlib.import_module(base)
        caplog.set_level(logging.WARNING, logger=optional_dependencies.__name__)
        module = optional_dependencies.import_optional(name)
        assert module.__name__ == name
        assert not caplog.records
    finally:
        if orig_mod is not None:
            sys.modules[name] = orig_mod
        else:
            sys.modules.pop(name, None)
        if orig_fallback is not None:
            optional_dependencies._fallbacks[name] = orig_fallback


def test_import_optional_returns_stub_when_missing(monkeypatch, caplog):
    name = "cryptography.fernet"
    monkeypatch.delitem(sys.modules, "cryptography", raising=False)
    monkeypatch.delitem(sys.modules, name, raising=False)
    monkeypatch.setitem(
        optional_dependencies._fallbacks,
        name,
        lambda: optional_dependencies._simple_module(
            name, Fernet=optional_dependencies._DummyFernet
        ),
    )

    def fake_import(module_name, package=None):
        raise ModuleNotFoundError(module_name)

    monkeypatch.setattr(importlib, "import_module", fake_import)
    caplog.set_level(logging.WARNING, logger=optional_dependencies.__name__)
    module = optional_dependencies.import_optional(name)
    assert module.Fernet is optional_dependencies._DummyFernet
    assert not caplog.records

def test_import_optional_logs_missing_package(monkeypatch, caplog):
    name = "cryptography.fernet"
    monkeypatch.delitem(sys.modules, "cryptography", raising=False)
    monkeypatch.delitem(sys.modules, name, raising=False)

    def fake_import(module_name, package=None):
        raise ModuleNotFoundError(module_name)

    monkeypatch.setattr(importlib, "import_module", fake_import)
    caplog.set_level(logging.INFO, logger=optional_dependencies.__name__)
    optional_dependencies.import_optional(name)
    assert any(
        record.levelno == logging.INFO
        and record.getMessage() == f"Optional dependency '{name}' is not installed"
        for record in caplog.records
    )


def test_import_optional_logs_internal_error(monkeypatch, caplog):
    name = "cryptography.fernet"

    def fake_import(module_name, package=None):
        raise NameError("boom")

    monkeypatch.setattr(importlib, "import_module", fake_import)
    caplog.set_level(logging.ERROR, logger=optional_dependencies.__name__)
    optional_dependencies.import_optional(name)
    assert any(
        record.levelno == logging.ERROR
        and record.getMessage() == f"Error importing optional dependency '{name}': boom"
        for record in caplog.records
    )

