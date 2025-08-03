#!/usr/bin/env python3
"""Generate strong random secret values for development.

Writes the values to an env file rather than printing them to stdout.
"""

import argparse
import logging
import secrets
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError


def _store_secret(client: boto3.client, name: str, value: str) -> None:
    """Create or update a secret in AWS Secrets Manager."""
    try:
        client.create_secret(Name=name, SecretString=value)
        logging.info("created secret %s", name)
    except client.exceptions.ResourceExistsException:
        client.put_secret_value(SecretId=name, SecretString=value)
        logging.info("updated secret %s", name)

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate development secrets")
    parser.add_argument(
        "--output", default="dev_secrets.env", help="file to write secrets"
    )
    args = parser.parse_args()

    secret_key = secrets.token_urlsafe(32)
    db_password = secrets.token_urlsafe(32)
    # Use Path.open to ensure UTF-8 encoding
    with Path(args.output).open("w", encoding="utf-8") as fh:
        fh.write(f"SECRET_KEY={secret_key}\n")
        fh.write(f"DB_PASSWORD={db_password}\n")
    logging.basicConfig(level=logging.INFO)
    logging.info("generated secrets written to %s", args.output)

    try:
        client = boto3.client("secretsmanager")
        _store_secret(client, "dev/SECRET_KEY", secret_key)
        _store_secret(client, "dev/DB_PASSWORD", db_password)
    except (BotoCoreError, ClientError) as exc:
        logging.debug("skipping AWS Secrets Manager update: %s", exc)


if __name__ == "__main__":
    main()
