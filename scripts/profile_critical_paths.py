#!/usr/bin/env python3
"""Run profiling on critical code paths and output reports.

This script profiles representative operations using Python's built-in
``cProfile`` and stores both a machine-readable ``.prof`` file and a
human-readable ``.txt`` summary. Extend ``critical_function`` with
project-specific logic to profile real code paths.
"""

from __future__ import annotations

import cProfile
import pstats
import time
from pathlib import Path

OUTPUT_PROF = Path("profiling_report.prof")
OUTPUT_TXT = Path("profiling_report.txt")


def critical_function() -> None:
    """Simulate a critical path within the application."""
    time.sleep(0.05)
    sum(i * i for i in range(1000))


def run() -> None:
    """Execute the profiled critical function."""
    critical_function()


if __name__ == "__main__":
    pr = cProfile.Profile()
    pr.enable()
    run()
    pr.disable()
    pr.dump_stats(str(OUTPUT_PROF))
    with OUTPUT_TXT.open("w", encoding="utf-8") as f:
        ps = pstats.Stats(pr, stream=f)
        ps.sort_stats(pstats.SortKey.TIME)
        ps.print_stats()
