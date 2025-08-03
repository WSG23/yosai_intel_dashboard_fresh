#!/usr/bin/env python3
"""Generate development secrets and store them in a secret manager.

Instead of writing raw secret values to disk, this script stores the
generated secrets in HashiCorp Vault or AWS Secrets Manager and writes
*references* to an env file. This keeps the actual values out of the
repository and local files while still allowing services to load them via
environment-specific injection.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import secrets
from pathlib import Path
from typing import Dict

try:  # optional dependencies for secret backends
    import hvac  # type: ignore
except Exception:  # pragma: no cover - dependency is optional
    hvac = None

try:  # pragma: no cover - dependency is optional
    import boto3  # type: ignore
except Exception:  # pragma: no cover - dependency is optional
    boto3 = None


def _store_in_vault(path: str, data: Dict[str, str]) -> None:
    if not hvac:
        raise RuntimeError("hvac is required for Vault operations")
    client = hvac.Client(
        url=os.getenv("VAULT_ADDR"), token=os.getenv("VAULT_TOKEN")
    )
    client.secrets.kv.v2.create_or_update_secret(path=path, secret=data)


def _store_in_aws(name: str, data: Dict[str, str]) -> None:
    if not boto3:
        raise RuntimeError("boto3 is required for AWS operations")
    client = boto3.client("secretsmanager", region_name=os.getenv("AWS_REGION"))
    client.create_secret(Name=name, SecretString=json.dumps(data))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate development secrets")
    parser.add_argument(
        "--backend",
        choices=["vault", "aws"],
        default="vault",
        help="secret backend to write to",
    )
    parser.add_argument(
        "--path",
        default="dev/dashboard",
        help="secret path or name in the backend",
    )
    parser.add_argument(
        "--output",
        default="dev_secrets.env",
        help="file to write secret references",
    )
    args = parser.parse_args()

    secret_key = secrets.token_urlsafe(32)
    db_password = secrets.token_urlsafe(32)
    data = {"SECRET_KEY": secret_key, "DB_PASSWORD": db_password}

    if args.backend == "vault":
        _store_in_vault(args.path, data)
        ref_prefix = f"vault:{args.path}#"
    else:
        _store_in_aws(args.path, data)
        ref_prefix = f"aws-secrets:{args.path}#"

    with Path(args.output).open("w", encoding="utf-8") as fh:
        for key in data:
            fh.write(f"{key}={ref_prefix}{key}\n")

    logging.basicConfig(level=logging.INFO)
    logging.info("secret references written to %s", args.output)


if __name__ == "__main__":
    main()

