#!/usr/bin/env python3
"""Command line tool to configure A/B testing weights."""

import argparse
from typing import Dict

from yosai_intel_dashboard.models.ml import ModelRegistry

from yosai_intel_dashboard.src.services.ab_testing import ModelABTester


def parse_weights(value: str) -> Dict[str, float]:
    weights: Dict[str, float] = {}
    for item in value.split(","):
        if not item:
            continue
        version, weight = item.split("=")
        weights[version] = float(weight)
    return weights


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Set traffic weights for model A/B testing"
    )
    parser.add_argument("model", help="Model name")
    parser.add_argument("weights", help="Comma separated version=weight pairs")
    parser.add_argument(
        "--db",
        dest="db",
        default="sqlite:///models.db",
        help="Model registry database URL",
    )
    parser.add_argument(
        "--bucket", dest="bucket", default="models", help="S3 bucket for artifacts"
    )
    parser.add_argument(
        "--weights-file",
        dest="weights_file",
        default="ab_weights.json",
        help="Weights JSON file",
    )
    args = parser.parse_args()

    registry = ModelRegistry(args.db, args.bucket)
    tester = ModelABTester(args.model, registry, weights_file=args.weights_file)
    tester.set_weights(parse_weights(args.weights))
    print(f"Updated weights for {args.model}: {tester.weights}")


if __name__ == "__main__":
    main()
