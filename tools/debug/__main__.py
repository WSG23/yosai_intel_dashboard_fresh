"""Unified CLI for debug helpers."""

from __future__ import annotations

import argparse
from typing import Iterable

from .assets import debug_navbar_icons
from .callbacks import debug_callback_conflicts, validate_callback_system


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run debug diagnostics")
    sub = parser.add_subparsers(dest="command")

    assets_p = sub.add_parser("assets", help="Check navbar assets")
    assets_p.add_argument(
        "icons", nargs="*", metavar="ICON", help="Icon names without .png"
    )

    sub.add_parser("callbacks", help="Run callback diagnostics")

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "assets":
        debug_navbar_icons(args.icons or None)
        return
    if args.command == "callbacks":
        debug_callback_conflicts()
        validate_callback_system()
        return

    # default: run all
    debug_navbar_icons(None)
    debug_callback_conflicts()
    validate_callback_system()


if __name__ == "__main__":  # pragma: no cover - manual tool
    main()
