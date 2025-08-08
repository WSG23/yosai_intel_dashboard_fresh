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
