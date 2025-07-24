"""Register Avro schemas with the Confluent Schema Registry."""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests

SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")
HEADERS = {"Content-Type": "application/vnd.schemaregistry.v1+json"}


def register_schema(file_path: Path) -> bool:
    """Register a single schema file.

    Parameters
    ----------
    file_path:
        Path to the ``.avsc`` file.
    Returns
    -------
    bool
        ``True`` on success, ``False`` otherwise.
    """
    subject = f"{file_path.stem}-value"
    with open(file_path, "r", encoding="utf-8") as fh:
        schema_str = fh.read()

    payload = json.dumps({"schema": schema_str})
    url = f"{SCHEMA_REGISTRY_URL}/subjects/{subject}/versions"
    response = requests.post(url, headers=HEADERS, data=payload, timeout=10)
    if response.status_code >= 300:
        logger.error(
            f"Failed to register {subject}: {response.status_code} {response.text}"
        )
        return False

    # Try to read version from response, otherwise fetch it
    version = response.json().get("version")
    if version is None:
        vers_resp = requests.get(url.rsplit("/", 1)[0] + "/versions", timeout=10)
        if vers_resp.status_code >= 300:
            logger.error(
                f"Failed retrieving version for {subject}: {vers_resp.status_code} {vers_resp.text}"
            )
            return False
        version = max(vers_resp.json())

    logger.info(f"Registered {subject} version {version}")
    return True


def main() -> int:
    schema_dir = Path(__file__).resolve().parent.parent / "schemas"
    ok = True
    for path in sorted(schema_dir.glob("*.avsc")):
        if not register_schema(path):
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
