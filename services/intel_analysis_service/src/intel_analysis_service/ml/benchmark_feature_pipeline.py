"""Benchmark utilities for :mod:`feature_pipeline`.

This script generates synthetic event streams to measure the performance
of :func:`build_context_features` on large datasets.  It compares the
standard pandas merge implementation with the optional pyarrow-based
implementation when pyarrow is available.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

import sys
sys.path.append(str(Path(__file__).resolve().parent))
from feature_pipeline import build_context_features, _HAVE_ARROW  # type: ignore


def _make_stream(name: str, n: int) -> pd.DataFrame:
    ts = pd.date_range("2024-01-01", periods=n, freq="min")
    data = np.random.rand(n)
    return pd.DataFrame({"timestamp": ts, name: data})


def run_benchmark(n: int = 100_000) -> Dict[str, float]:
    weather = _make_stream("weather", n)
    events = _make_stream("events", n)
    transport = _make_stream("transport", n)
    social = _make_stream("social", n)
    infra = _make_stream("infra", n)

    start = time.perf_counter()
    build_context_features(
        weather, events, transport, social, infra, use_pyarrow=False
    )
    pandas_time = time.perf_counter() - start

    arrow_time = None
    if _HAVE_ARROW:
        start = time.perf_counter()
        build_context_features(
            weather, events, transport, social, infra, use_pyarrow=True
        )
        arrow_time = time.perf_counter() - start

    return {"pandas": pandas_time, "pyarrow": arrow_time}


if __name__ == "__main__":
    results = run_benchmark()
    print("Benchmark results (seconds):")
    for k, v in results.items():
        if v is not None:
            print(f"  {k:7s}: {v:.3f}")
        else:
            print(f"  {k:7s}: not run")
