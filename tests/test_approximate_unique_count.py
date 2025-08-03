from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import redis

# Load the module directly to avoid heavy package imports
spec = importlib.util.spec_from_file_location(
    "approximation",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard"
    / "src"
    / "services"
    / "analytics"
    / "approximation.py",
)
approx_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(approx_module)
approximate_unique_count = approx_module.approximate_unique_count


def test_approximate_unique_count_small():
    series = pd.Series([1, 2, 2, 3, 4])
    assert approximate_unique_count(series) == 4


def test_approximate_unique_count_large():
    # 50k unique values, each repeated twice
    series = pd.Series(np.repeat(np.arange(50000), 2))
    estimate = approximate_unique_count(series)
    assert abs(estimate - 50000) / 50000 < 0.1
