#!/usr/bin/env python3
"""Command line wrapper for :class:`MigrationManager`."""
from __future__ import annotations

import argparse
import logging
from typing import List

from yosai_intel_dashboard.src.database.migrations import MigrationManager

LOG = logging.getLogger(__name__)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Manage database migrations via Alembic"
    )
    parser.add_argument(
        "--config",
        default="migrations/alembic.ini",
        help="Path to alembic configuration file",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    up = sub.add_parser("upgrade", help="Upgrade to latest or given revision")
    up.add_argument("revision", nargs="?", default="head")

    down = sub.add_parser("downgrade", help="Downgrade to a specific revision")
    down.add_argument("revision")

    sub.add_parser("rollback", help="Rollback the last applied migration")
    sub.add_parser("current", help="Show the current revision")

    args = parser.parse_args(argv)
    mgr = MigrationManager(args.config)

    if args.command == "upgrade":
        mgr.upgrade(args.revision)
    elif args.command == "downgrade":
        mgr.downgrade(args.revision)
    elif args.command == "rollback":
        mgr.rollback()
    elif args.command == "current":
        mgr.current()
    else:
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
