"""CLI to inspect detected N+1 queries."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from yosai_intel_dashboard.src.core.performance import profiler


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Show detected N+1 queries")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    args = parser.parse_args(argv)

    data = profiler.get_n_plus_one_queries()

    if args.json:
        print(json.dumps(data, indent=2, default=str))
        return

    if not data:
        print("No N+1 queries detected")
        return

    for endpoint, entries in data.items():
        print(f"Endpoint: {endpoint}")
        for entry in entries:
            print(f"  Query: {entry['query']}")
            for stack in entry["stacks"]:
                print("  Stack trace:")
                print(stack)


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()

