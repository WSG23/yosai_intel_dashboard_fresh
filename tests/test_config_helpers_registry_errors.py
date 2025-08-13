"""Tests ensuring ``config_helpers`` gracefully handles registry issues."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def _load_helpers():
    path = (
        Path(__file__).resolve().parents[1]
        / "yosai_intel_dashboard"
        / "src"
        / "core"
        / "utils"
        / "config_helpers.py"
    )
    spec = importlib.util.spec_from_file_location(
        "yosai_intel_dashboard.src.core.utils.config_helpers", path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "broken_registry",
    [object(), SimpleNamespace(get=None), SimpleNamespace(get=lambda name: None)],
)
def test_helpers_fallback_when_registry_invalid(monkeypatch, broken_registry) -> None:
    helpers = _load_helpers()
    monkeypatch.setattr(helpers, "registry", broken_registry)
    assert helpers.get_ai_confidence_threshold() == 0.8
    assert helpers.get_max_upload_size_mb() == 100
    assert helpers.get_upload_chunk_size() == 50000

