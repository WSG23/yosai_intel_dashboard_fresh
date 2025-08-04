"""Wrapper exposing :mod:`yosai_intel_dashboard.src.adapters.api`.

This module previously used ``import *`` to mirror all contents of
``yosai_intel_dashboard.src.adapters.api``. To maintain a consistent coding
style and avoid wildcard imports, we now load the target module explicitly and
re-export it via ``sys.modules``. Importers of ``api`` will transparently receive
the original adapter module without polluting this module's namespace.
"""

from __future__ import annotations

import sys
from importlib import import_module

_api = import_module("yosai_intel_dashboard.src.adapters.api")

# Re-export the adapter module so ``import api`` works as before.
sys.modules[__name__] = _api

