#!/usr/bin/env python3
"""CLI to check Kafka cluster health."""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from yosai_intel_dashboard.src.infrastructure.monitoring import (  # noqa: E402
    check_cluster_health,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Display Kafka cluster health information"
    )
    parser.add_argument(
        "--brokers",
        default="localhost:9092",
        help="Bootstrap servers (host:port list)",
    )
    args = parser.parse_args()

    health = check_cluster_health(args.brokers)
    print(json.dumps(health, indent=2))


if __name__ == "__main__":
    main()
