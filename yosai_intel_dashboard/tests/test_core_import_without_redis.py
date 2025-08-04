"""Ensure core package imports without Redis installed."""

from __future__ import annotations

import importlib
import sys


def test_core_import_without_redis(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "redis", None)
    monkeypatch.setitem(sys.modules, "redis.asyncio", None)
    sys.modules.pop("yosai_intel_dashboard.src.core", None)
    module = importlib.import_module("yosai_intel_dashboard.src.core")
    assert module
