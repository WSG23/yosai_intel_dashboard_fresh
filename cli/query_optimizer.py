#!/usr/bin/env python3
"""CLI to generate database query optimization reports."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from services.query_optimizer import QueryOptimizer


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run query optimization report")
    parser.add_argument("logfile", help="Path to database log file to analyze")
    args = parser.parse_args(argv)

    optimizer = QueryOptimizer()
    slow_queries = optimizer.parse_logs(args.logfile)
    report = []
    for item in slow_queries:
        analysis = optimizer.analyze_query(item.query)
        report.append(
            {
                "query": item.query,
                "duration": item.duration,
                "plan": analysis.get("plan"),
                "recommendations": analysis.get("recommendations"),
            }
        )
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
