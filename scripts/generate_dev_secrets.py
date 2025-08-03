#!/usr/bin/env python3
"""Generate strong random secret values for development.

Writes the values to an env file rather than printing them to stdout.
"""

import argparse
import logging
import secrets
from pathlib import Path

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


if __name__ == "__main__":
    main()
