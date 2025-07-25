#!/usr/bin/env python3
"""Check repository Avro schemas against the Schema Registry."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from requests.exceptions import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import importlib.util

spec = importlib.util.spec_from_file_location(
    "schema_registry", ROOT / "services" / "common" / "schema_registry.py"
)
schema_registry = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = schema_registry
spec.loader.exec_module(schema_registry)
SchemaRegistryClient = schema_registry.SchemaRegistryClient


def main() -> int:
    schema_dir = Path("schemas/avro")
    client = SchemaRegistryClient()
    ok = True
    for path in sorted(schema_dir.glob("*.avsc")):
        subject = f"{path.stem}-value"
        schema = json.loads(path.read_text())
        try:
            compatible = client.check_compatibility(subject, schema, version="latest")
        except HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                print(f"No existing schema for {subject}, skipping check.")
                continue
            print(f"Failed compatibility check for {subject}: {exc}", file=sys.stderr)
            ok = False
            continue
        if not compatible:
            print(f"Incompatible schema for {subject}", file=sys.stderr)
            ok = False
    if ok:
        print("All schemas compatible with registry.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
