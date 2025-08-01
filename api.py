"""Wrapper exposing :mod:`yosai_intel_dashboard.src.adapters.api`."""

import sys

from yosai_intel_dashboard.src.adapters.api import *

# If app exists in the module, make it available
try:
    from yosai_intel_dashboard.src.adapters.api import app  # type: ignore
except Exception:
    pass

sys.modules[__name__] = sys.modules["yosai_intel_dashboard.src.adapters.api"]
