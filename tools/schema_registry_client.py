#!/usr/bin/env python3
"""Lightweight client for interacting with a Confluent Schema Registry.

This utility registers Avro schemas and fetches registered schemas
without requiring the full Confluent Python client. It is intended for
use in CI and local development where only basic HTTP access to the
registry is needed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import requests


def register_schema(registry: str, subject: str, schema_path: str) -> dict[str, Any]:
    """Register a schema file under the given subject."""
    schema = Path(schema_path).read_text()
    payload = {"schema": schema}
    response = requests.post(
        f"{registry.rstrip('/')}/subjects/{subject}/versions",
        headers={"Content-Type": "application/vnd.schemaregistry.v1+json"},
        data=json.dumps(payload),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def get_latest_schema(registry: str, subject: str) -> dict[str, Any]:
    """Fetch the latest schema registered under *subject*."""
    response = requests.get(
        f"{registry.rstrip('/')}/subjects/{subject}/versions/latest",
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="Interact with schema registry")
    parser.add_argument("registry", help="Schema registry URL, e.g. http://localhost:8081")
    subparsers = parser.add_subparsers(dest="command", required=True)

    reg = subparsers.add_parser("register", help="Register a new schema version")
    reg.add_argument("subject", help="Schema subject name")
    reg.add_argument("file", help="Path to Avro schema file")

    fetch = subparsers.add_parser("get", help="Fetch latest schema")
    fetch.add_argument("subject", help="Schema subject name")

    args = parser.parse_args()
    if args.command == "register":
        info = register_schema(args.registry, args.subject, args.file)
        print(json.dumps(info, indent=2))
    else:
        info = get_latest_schema(args.registry, args.subject)
        print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
