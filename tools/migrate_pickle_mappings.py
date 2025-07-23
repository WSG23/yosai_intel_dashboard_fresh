"""Legacy pickle to JSON migration utility.

This script converts a ``learned_mappings.pkl`` file into a JSON file
compatible with
:class:`services.learning.src.api.consolidated_service.ConsolidatedLearningService`.

**Important**: Pickle files are inherently insecure and support for them has
been removed from the dashboard. Convert any existing pickle mapping files to
JSON and remove the pickle versions from your deployment.

.. warning::
    Only run this script on pickle files from trusted sources. Loading
    pickle data from an untrusted location can execute arbitrary code.

Usage::

    python tools/migrate_pickle_mappings.py [--remove-pickle] \
        /path/to/learned_mappings.pkl

The JSON output will be written next to the pickle file using the
``.json`` extension. When ``--remove-pickle`` is supplied the original pickle
file is deleted after a successful conversion.
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path


def migrate(pkl_file: Path) -> Path:
    """Convert ``pkl_file`` to JSON and return the new path."""

    if not pkl_file.exists():
        raise FileNotFoundError(pkl_file)

    with open(pkl_file, "rb") as fh:
        data = pickle.load(fh)

    json_file = pkl_file.with_suffix(".json")
    with open(json_file, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)

    return json_file


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(description="Migrate pickle mappings to JSON")
    parser.add_argument("pickle_file", help="Path to learned_mappings.pkl")
    parser.add_argument(
        "--remove-pickle",
        action="store_true",
        help="Delete the pickle file after successful conversion",
    )
    args = parser.parse_args(argv[1:])

    pkl_path = Path(args.pickle_file)
    try:
        json_path = migrate(pkl_path)
    except Exception as exc:
        print(f"Failed to migrate {pkl_path}: {exc}")
        raise SystemExit(1)

    if args.remove_pickle:
        try:
            pkl_path.unlink()
            print(f"Removed {pkl_path}")
        except Exception as exc:  # pragma: no cover - manual removal
            print(f"Failed to remove {pkl_path}: {exc}")

    print(f"Wrote JSON mappings to {json_path}")


if __name__ == "__main__":  # pragma: no cover - manual utility
    main(sys.argv)
