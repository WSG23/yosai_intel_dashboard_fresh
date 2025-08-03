from __future__ import annotations

import hashlib
import math

import pandas as pd


def _leading_zero_count(x: int, bits: int) -> int:
    if x == 0:
        return bits
    return bits - x.bit_length()


def approximate_unique_count(series: pd.Series, precision: int = 14) -> int:
    """Estimate unique values using a HyperLogLog sketch.

    The algorithm uses a fixed number of registers determined by ``precision``
    (``m = 2**precision``) and processes each element without storing the full
    set of values, making it suitable for large datasets.
    """

    m = 1 << precision
    registers = [0] * m
    for value in series.dropna():
        h = int(hashlib.sha1(str(value).encode("utf-8")).hexdigest(), 16)
        idx = h & (m - 1)
        w = h >> precision
        rank = _leading_zero_count(w, 160 - precision) + 1
        if rank > registers[idx]:
            registers[idx] = rank
    alpha = 0.7213 / (1 + 1.079 / m)
    indicator = sum(2.0**-r for r in registers)
    estimate = alpha * m * m / indicator
    if estimate <= 2.5 * m:
        v = registers.count(0)
        if v > 0:
            estimate = m * math.log(m / v)
    return int(estimate)


__all__ = ["approximate_unique_count"]
