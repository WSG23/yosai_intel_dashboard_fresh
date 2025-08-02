"""Lightweight entry point for utility helpers."""
import importlib
from pathlib import Path
from typing import Any

# Point package path to the source utilities directory without importing it.
__path__ = [
    str(Path(__file__).resolve().parents[1] / "yosai_intel_dashboard" / "src" / "utils")
]


def __getattr__(name: str) -> Any:  # pragma: no cover - thin proxy
    pkg = importlib.import_module("yosai_intel_dashboard.src.utils")
    return getattr(pkg, name)
