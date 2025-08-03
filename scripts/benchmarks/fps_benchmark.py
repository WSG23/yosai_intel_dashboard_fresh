"""Benchmark to estimate frames per second for chart generation."""

from __future__ import annotations

import time
from typing import Sequence

import numpy as np

from yosai_intel_dashboard.src.infrastructure.monitoring.visualization import (
    drift_chart,
)


def measure_fps(iterations: int = 100, points: int = 100) -> float:
    """Render ``iterations`` charts and return the achieved FPS."""
    data: Sequence[float] = np.random.rand(points)
    start = time.perf_counter()
    for _ in range(iterations):
        drift_chart(data)
    elapsed = time.perf_counter() - start
    fps = iterations / elapsed
    print(f"Generated {iterations} frames in {elapsed:.2f}s ({fps:.2f} FPS)")
    return fps


if __name__ == "__main__":
    measure_fps()
