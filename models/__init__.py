"""Utilities for loading deployed models.

This module exposes a :func:`load_model` helper used by deployment
code to fetch a model implementation for a given version.  The metadata
for available models is stored in ``registry.json`` within this package.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, Any

_REGISTRY_PATH = Path(__file__).with_name("registry.json")


def _read_registry() -> Dict[str, Any]:
    if _REGISTRY_PATH.exists():
        with _REGISTRY_PATH.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def load_model(version: str, name: str = "demo") -> Callable[[float], float]:
    """Load and return a callable model implementation for ``version``.

    Parameters
    ----------
    version:
        The version identifier of the model to load.
    name:
        Optional model name.  Defaults to ``"demo"`` which is used in tests.

    Returns
    -------
    Callable[[float], float]
        A simple callable representing the model.  For demonstration
        purposes models are represented as ``lambda`` functions that scale
        the input by a factor defined in :mod:`registry.json`.
    """

    registry = _read_registry()
    info = registry.get(name, {}).get("versions", {}).get(version)
    if info is None:
        raise ValueError(f"Unknown model {name} version {version}")
    factor = float(info.get("factor", 1.0))
    return lambda x, factor=factor: x * factor

__all__ = ["load_model"]
