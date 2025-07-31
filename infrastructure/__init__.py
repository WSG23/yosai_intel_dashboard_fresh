"""Infrastructure package for application utilities."""

from importlib import import_module as _im
import sys as _sys

communication = _im('yosai_intel_dashboard.src.infrastructure.communication')
_sys.modules.setdefault(__name__ + '.communication', communication)

from . import discovery

__all__ = ["communication", "discovery"]
