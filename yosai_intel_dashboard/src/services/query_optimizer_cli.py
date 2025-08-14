"""CLI interface for :class:`QueryOptimizer`."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from yosai_intel_dashboard.src.core.logging import get_logger
from yosai_intel_dashboard.src.services.query_optimizer import QueryOptimizer

logger = get_logger(__name__)

def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Query optimizer utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    suggest_p = subparsers.add_parser(
        "suggest", help="Show index suggestions for a SQL query"
    )
    suggest_p.add_argument("query", help="SQL query to analyze")

    migrate_p = subparsers.add_parser(
        "migrate", help="Write index suggestions to a migration file"
    )
    migrate_p.add_argument("query", help="SQL query to analyze")
    migrate_p.add_argument("output", help="File to write migration SQL")

    args = parser.parse_args(argv)

    optimizer = QueryOptimizer()

    if args.command == "suggest":
        report = optimizer.generate_regression_report(args.query)
        logger.info("Index suggestion report", extra={"report": report})
    elif args.command == "migrate":
        suggestions = optimizer.suggest_indexes(args.query)
        if not suggestions:
            logger.info("No index suggestions", extra={"query": args.query})
            return
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(";\n".join(suggestions) + ";\n")
        logger.info("Wrote migration script", extra={"output": args.output})


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
