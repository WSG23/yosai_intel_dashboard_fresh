from __future__ import annotations

"""Lightweight CPU and memory profiler using ``psutil``."""

import argparse
import json
import subprocess
import time
from typing import Dict, List

import psutil


def profile_pid(pid: int, interval: float, duration: float) -> List[Dict[str, float]]:
    """Collect CPU and RSS memory usage for the given process."""
    proc = psutil.Process(pid)
    data = []
    end = time.time() + duration
    while time.time() < end:
        cpu = proc.cpu_percent(interval=interval)
        rss = proc.memory_info().rss / (1024 * 1024)
        data.append({"timestamp": time.time(), "cpu_percent": cpu, "rss_mb": rss})
    return data


def profile_command(
    cmd: List[str], interval: float, duration: float
) -> List[Dict[str, float]]:
    """Run ``cmd`` as a subprocess and profile it."""
    proc = subprocess.Popen(cmd)
    try:
        return profile_pid(proc.pid, interval, duration)
    finally:
        proc.terminate()
        proc.wait()


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile a process with psutil")
    parser.add_argument("target", nargs="+", help="PID or command to execute")
    parser.add_argument(
        "--interval", type=float, default=1.0, help="Sampling interval in seconds"
    )
    parser.add_argument(
        "--duration", type=float, default=10.0, help="Total profiling time in seconds"
    )
    parser.add_argument("--output", help="Optional JSON output file")
    args = parser.parse_args()

    if len(args.target) == 1 and args.target[0].isdigit():
        records = profile_pid(int(args.target[0]), args.interval, args.duration)
    else:
        records = profile_command(args.target, args.interval, args.duration)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(records, f, indent=2)
    else:
        for r in records:
            print(
                f"{r['timestamp']:.0f} cpu={r['cpu_percent']:.1f}% rss={r['rss_mb']:.1f}MB"
            )


if __name__ == "__main__":
    main()
