"""Convenience wrapper for :mod:`yosai_intel_dashboard.src.core.domain.entities`."""

import sys

from yosai_intel_dashboard.src.core.domain.entities import *

# Make common exports available for older import paths
from yosai_intel_dashboard.src.core.domain.entities.base import BaseModel

sys.modules[__name__] = sys.modules[
    "yosai_intel_dashboard.src.core.domain.entities"
]

