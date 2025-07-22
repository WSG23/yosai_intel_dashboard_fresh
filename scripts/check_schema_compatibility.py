#!/usr/bin/env python3
"""Validate Avro schemas in the repository."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from fastavro import parse_schema


def main() -> int:
    schema_dir = Path("schemas/avro")
    ok = True
    for path in sorted(schema_dir.glob("*.avsc")):
        try:
            schema = json.loads(path.read_text())
            parse_schema(schema)
        except Exception as exc:
            print(f"Invalid schema {path.name}: {exc}", file=sys.stderr)
            ok = False
    if ok:
        print("All schemas valid.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
