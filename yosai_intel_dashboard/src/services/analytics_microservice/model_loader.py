from __future__ import annotations

"""Deprecated module. Use :mod:`services.common.analytics_utils` instead."""

import warnings

from yosai_intel_dashboard.src.services.common.analytics_utils import (
    preload_active_models,
)

warnings.warn(
    "services.analytics.model_loader is deprecated; use"
    " services.common.analytics_utils.preload_active_models",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["preload_active_models"]
