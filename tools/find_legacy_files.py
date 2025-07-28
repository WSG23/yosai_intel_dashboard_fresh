"""CLI to find potential legacy files."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from tools.legacy_utils import IGNORE_DIRS, scan_legacy_files


def main() -> None:
    parser = argparse.ArgumentParser(description="Find potential legacy files")
    parser.add_argument("--delete", action="store_true", help="Delete matched files")
    args = parser.parse_args()

    for path, reasons in scan_legacy_files(Path("."), ignore_dirs=IGNORE_DIRS):
        print(f"{path}  # {', '.join(reasons)}")
        if args.delete:
            try:
                os.remove(path)
                print(f"Removed {path}")
            except OSError as exc:
                print(f"Failed to remove {path}: {exc}")


if __name__ == "__main__":
    main()
