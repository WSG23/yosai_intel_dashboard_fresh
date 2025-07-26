"""Compatibility layer exposing src infrastructure modules."""
from __future__ import annotations
from pathlib import Path

__path__.append(str(Path(__file__).resolve().parents[1] / "yosai_intel_dashboard" / "src" / "infrastructure"))
