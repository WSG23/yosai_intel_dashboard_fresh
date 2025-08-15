"""HyperLogLog-based distinct counting utilities."""

from __future__ import annotations

import pandas as pd
from hyperloglog import HyperLogLog


def hll_count(series: pd.Series, error_rate: float = 0.01) -> int:
    """Estimate the number of unique items in ``series`` using HyperLogLog.

    Parameters
    ----------
    series:
        Series containing values whose distinct count is desired.
    error_rate:
        Relative error rate for the HyperLogLog counter.

    Returns
    -------
    int
        Estimated cardinality of the series.
    """

    hll = HyperLogLog(error_rate)
    for value in series.dropna():
        hll.add(str(value).encode("utf-8"))
    return int(len(hll))


__all__ = ["hll_count"]
