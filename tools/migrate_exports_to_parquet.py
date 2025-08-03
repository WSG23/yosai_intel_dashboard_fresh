"""Utility to migrate legacy CSV/JSON exports to Parquet."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def _convert(path: Path, remove: bool) -> None:
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        df = pd.read_json(path)
    out = path.with_suffix(".parquet")
    df.to_parquet(out, index=False)
    if remove:
        path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate exports to Parquet")
    parser.add_argument("export_dir", help="Directory containing legacy exports")
    parser.add_argument(
        "--remove-original",
        action="store_true",
        help="Delete original files after successful conversion",
    )
    args = parser.parse_args()
    base = Path(args.export_dir)
    for ext in ("csv", "json"):
        for file in base.rglob(f"*.{ext}"):
            _convert(file, args.remove_original)


if __name__ == "__main__":
    main()
