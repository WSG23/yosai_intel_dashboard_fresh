"""CLI to analyze and create database indexes."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from yosai_intel_dashboard.src.core.logging import get_logger
from yosai_intel_dashboard.src.database.index_optimizer import IndexOptimizer

logger = get_logger(__name__)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Database index optimizer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("analyze", help="Show index usage statistics")

    create_p = subparsers.add_parser("create", help="Create index if missing")
    create_p.add_argument("table", help="Table name")
    create_p.add_argument("columns", nargs="+", help="Column names")

    args = parser.parse_args(argv)

    optimizer = IndexOptimizer()

    if args.command == "analyze":
        stats = optimizer.analyze_index_usage()
        logger.info("Index usage statistics", extra={"stats": stats})
    elif args.command == "create":
        statements = optimizer.recommend_new_indexes(args.table, args.columns)
        if not statements:
            logger.info(
                "No indexes to create", extra={"table": args.table, "columns": args.columns}
            )
            return
        for sql in statements:
            logger.info("Executing index creation", extra={"sql": sql})
        optimizer.apply_recommendations(args.table, args.columns)
        logger.info("Created index", extra={"table": args.table, "columns": args.columns})


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
