
"""Expose legacy :mod:`security` package under ``src`` namespace."""

from __future__ import annotations

from pathlib import Path

__path__.append(str(Path(__file__).resolve().parents[4] / "security"))
