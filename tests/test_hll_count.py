from __future__ import annotations

import pandas as pd

from services.analytics.core.utils import hll_count


def test_hll_count_small_series():
    s = pd.Series(["a", "b", "b"])
    assert hll_count(s) == 2


def test_hll_count_large_series_accuracy():
    s = pd.Series([f"user{i}" for i in range(10000)])
    estimate = hll_count(s)
    assert abs(estimate - 10000) / 10000 < 0.05
