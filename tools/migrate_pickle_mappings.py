"""Legacy pickle to JSON migration utility.

This script converts a ``learned_mappings.pkl`` file into a JSON file
compatible with :class:`services.consolidated_learning_service.ConsolidatedLearningService`.

.. warning::
    Only run this script on pickle files from trusted sources. Loading
    pickle data from an untrusted location can execute arbitrary code.

Usage::

    python tools/migrate_pickle_mappings.py /path/to/learned_mappings.pkl

The JSON output will be written next to the pickle file using the
``.json`` extension.
"""
from __future__ import annotations

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
    if len(argv) != 2:
        print("Usage: python migrate_pickle_mappings.py <pickle_file>")
        raise SystemExit(1)

    pkl_path = Path(argv[1])
    try:
        json_path = migrate(pkl_path)
    except Exception as exc:
        print(f"Failed to migrate {pkl_path}: {exc}")
        raise SystemExit(1)

    print(f"Wrote JSON mappings to {json_path}")


if __name__ == "__main__":  # pragma: no cover - manual utility
    main(sys.argv)
