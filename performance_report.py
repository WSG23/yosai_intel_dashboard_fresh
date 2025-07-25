"""Utility to generate performance reports from load test results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt
import pandas as pd


def load_locust_stats(csv_path: Path) -> pd.DataFrame:
    """Load Locust statistics CSV."""
    return pd.read_csv(csv_path)


def load_k6_stats(json_path: Path) -> pd.DataFrame:
    """Load k6 summary JSON."""
    with open(json_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    metrics = data.get("metrics", {})
    rows: List[Tuple[str, float]] = []
    for name, m in metrics.items():
        if "p(95)" in m:
            rows.append((name, m["p(95)"], m.get("p(99)", 0)))
    return pd.DataFrame(rows, columns=["metric", "p95", "p99"])


def plot_latency(df: pd.DataFrame, title: str, output: Path) -> None:
    df.plot(x="metric", y=["p95", "p99"], kind="bar")
    plt.title(title)
    plt.ylabel("ms")
    plt.tight_layout()
    plt.savefig(output)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Path to locust CSV or k6 summary JSON")
    parser.add_argument("--type", choices=["locust", "k6"], default="locust")
    parser.add_argument("--output", default="report.png")
    args = parser.parse_args()

    path = Path(args.input)
    if args.type == "locust":
        df = load_locust_stats(path)
        df = df.rename(columns={"95%": "p95", "99%": "p99"})
        plot_latency(df, "Locust Latency", Path(args.output))
    else:
        df = load_k6_stats(path)
        plot_latency(df, "k6 Latency", Path(args.output))
    print(f"Report written to {args.output}")
