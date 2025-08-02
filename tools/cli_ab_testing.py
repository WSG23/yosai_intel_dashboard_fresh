"""Command line utilities for model A/B testing."""

import argparse
from typing import Dict

from yosai_intel_dashboard.src.services.ab_testing import ModelABTester
from yosai_intel_dashboard.models.ml import ModelRegistry


def parse_weights(value: str) -> Dict[str, float]:
    """Parse comma separated version=weight pairs."""
    weights: Dict[str, float] = {}
    for item in value.split(","):
        if not item:
            continue
        version, weight = item.split("=")
        weights[version] = float(weight)
    return weights


def _cmd_set(args: argparse.Namespace) -> None:
    registry = ModelRegistry(args.db, args.bucket)
    tester = ModelABTester(
        args.model,
        registry,
        weights_file=args.weights_file,
        metrics_file=args.metrics_file,
    )
    tester.set_weights(parse_weights(args.weights))
    print(f"Updated weights for {args.model}: {tester.weights}")


def _cmd_stats(args: argparse.Namespace) -> None:
    registry = ModelRegistry(args.db, args.bucket)
    tester = ModelABTester(
        args.model,
        registry,
        weights_file=args.weights_file,
        metrics_file=args.metrics_file,
    )
    if not tester.metrics:
        print("No metrics available")
        return
    for version, stats in tester.metrics.items():
        count = stats.get("count", 0)
        success = stats.get("success", 0)
        rate = success / count if count else 0.0
        latency = stats.get("latency_sum", 0.0) / count if count else 0.0
        print(
            f"{version}: count={int(count)} success={int(success)} "
            f"rate={rate:.2%} avg_latency={latency:.3f}s"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="A/B testing utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("model", help="Model name")
    common.add_argument(
        "--db",
        dest="db",
        default="sqlite:///models.db",
        help="Model registry database URL",
    )
    common.add_argument(
        "--bucket", dest="bucket", default="models", help="S3 bucket for artifacts"
    )
    common.add_argument(
        "--weights-file",
        dest="weights_file",
        default="ab_weights.json",
        help="Weights JSON file",
    )
    common.add_argument(
        "--metrics-file",
        dest="metrics_file",
        default="ab_metrics.json",
        help="Metrics JSON file",
    )

    p_set = sub.add_parser("set", parents=[common], help="Set traffic weights")
    p_set.add_argument("weights", help="Comma separated version=weight pairs")
    p_set.set_defaults(func=_cmd_set)

    p_stats = sub.add_parser(
        "stats", parents=[common], help="Show variant performance statistics"
    )
    p_stats.set_defaults(func=_cmd_stats)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

