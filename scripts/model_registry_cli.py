#!/usr/bin/env python3
"""Command line interface for the ``ModelRegistry``."""
from __future__ import annotations

import argparse
import logging
from typing import List

from yosai_intel_dashboard.models.ml.model_registry import ModelRegistry

LOG = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Interact with the model registry")
    parser.add_argument(
        "--db-url", default="sqlite:///model_registry.db", help="Database URL"
    )
    parser.add_argument(
        "--bucket", default="local-models", help="Bucket for model artifacts"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ls = sub.add_parser("list", help="List available versions for a model")
    ls.add_argument("name", help="Model name")

    activate = sub.add_parser("activate", help="Activate a specific model version")
    activate.add_argument("name", help="Model name")
    activate.add_argument("version", help="Version to activate")

    rollback = sub.add_parser("rollback", help="Rollback to previous version")
    rollback.add_argument("name", help="Model name")
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    registry = ModelRegistry(args.db_url, args.bucket)

    if args.command == "list":
        records = registry.list_models(args.name)
        if not records:
            print(f"No versions found for {args.name}")
            return 0
        for rec in records:
            acc = None
            if rec.metrics and "accuracy" in rec.metrics:
                acc = rec.metrics["accuracy"]
            flag = "*" if rec.is_active else " "
            print(f"{flag} {rec.version}\taccuracy={acc}\tdataset={rec.dataset_hash}")
        return 0

    if args.command == "activate":
        registry.set_active_version(args.name, args.version)
        print(f"Activated {args.name} version {args.version}")
        return 0

    if args.command == "rollback":
        rec = registry.rollback_to_previous(args.name)
        if rec is None:
            print(f"No previous version found for {args.name}")
        else:
            print(f"Rolled back {args.name} to version {rec.version}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
