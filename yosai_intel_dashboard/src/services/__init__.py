
"""Expose legacy :mod:`services` package under ``src`` namespace."""

from __future__ import annotations

from pathlib import Path

__path__.append(str(Path(__file__).resolve().parents[3] / "services"))
