from __future__ import annotations

import argparse
import asyncio
import json
from typing import List

from yosai_intel_dashboard.src.core.logging import get_logger
from .framework import MigrationManager
from .strategies import AnalyticsMigration, EventsMigration, GatewayMigration

logger = get_logger(__name__)


def _build_manager(args: argparse.Namespace) -> MigrationManager:
    strategies = [
        GatewayMigration(args.gateway_dsn),
        EventsMigration(args.events_dsn),
        AnalyticsMigration(args.analytics_dsn),
    ]
    return MigrationManager(args.source_dsn, strategies)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Database migration manager")
    parser.add_argument("--source-dsn", default="postgresql:///yosai_db")
    parser.add_argument("--gateway-dsn", default="postgresql:///yosai_gateway_db")
    parser.add_argument("--events-dsn", default="postgresql:///yosai_events_db")
    parser.add_argument("--analytics-dsn", default="postgresql:///yosai_analytics_db")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run")
    sub.add_parser("rollback")
    sub.add_parser("status")

    args = parser.parse_args(argv)
    mgr = _build_manager(args)

    if args.cmd == "run":
        asyncio.run(mgr.migrate())
        return 0
    if args.cmd == "rollback":
        asyncio.run(mgr.rollback())
        return 0
    if args.cmd == "status":
        status = asyncio.run(mgr.status())
        logger.info("Migration status", extra={"status": status})
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
