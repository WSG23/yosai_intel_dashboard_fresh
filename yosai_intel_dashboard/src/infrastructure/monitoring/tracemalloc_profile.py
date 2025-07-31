from __future__ import annotations

"""Run a Python script and record memory allocations using ``tracemalloc``."""

import argparse
import runpy
import time
import tracemalloc


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a script with tracemalloc enabled"
    )
    parser.add_argument("script", help="Python module or script path to execute")
    parser.add_argument("--snapshot", help="Optional file to save the final snapshot")
    parser.add_argument(
        "--frames", type=int, default=25, help="Number of stack frames to capture"
    )
    args = parser.parse_args()

    tracemalloc.start(args.frames)
    start = time.perf_counter()
    runpy.run_path(args.script, run_name="__main__")
    duration = time.perf_counter() - start
    snapshot = tracemalloc.take_snapshot()

    top = snapshot.statistics("lineno")[:10]
    print(f"Executed {args.script} in {duration:.2f}s; top allocations:")
    for stat in top:
        print(stat)

    if args.snapshot:
        snapshot.dump(args.snapshot)
        print(f"Snapshot written to {args.snapshot}")


if __name__ == "__main__":
    main()
