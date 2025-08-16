from __future__ import annotations

"""Utility helpers for analytics services."""

import pandas as pd

try:  # pragma: no cover - optional dependency
    from hyperloglog import HyperLogLog
except Exception:  # pragma: no cover - the package may be missing
    HyperLogLog = None


def hll_count(series: pd.Series, error_rate: float = 0.01) -> int:
    """Estimate the number of unique items in ``series``.

    Uses the :mod:`hyperloglog` library when available. If the dependency is
    missing, falls back to :meth:`pandas.Series.nunique` for an exact count.

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

    if HyperLogLog is None:
        return int(series.nunique())

    hll = HyperLogLog(error_rate)
    for value in series.dropna():
        hll.add(str(value).encode("utf-8"))
    return int(len(hll))


__all__ = ["hll_count"]
