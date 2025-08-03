"""Benchmark to gauge rendering time as data size grows."""

from __future__ import annotations

import time
from typing import Iterable

import numpy as np

from yosai_intel_dashboard.src.infrastructure.monitoring.visualization import heatmap


def benchmark(sizes: Iterable[int] = (10, 100, 500, 1000)) -> None:
    for size in sizes:
        matrix = np.random.rand(size, size)
        start = time.perf_counter()
        heatmap(matrix)
        elapsed = time.perf_counter() - start
        print(f"{size}x{size} matrix: {elapsed:.3f}s")


if __name__ == "__main__":
    benchmark()
