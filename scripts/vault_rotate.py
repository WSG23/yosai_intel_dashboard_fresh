"""Rotate critical secrets stored in Vault."""
from __future__ import annotations

import os
import secrets

import hvac

DB_PATH = "secret/data/db"
JWT_PATH = "secret/data/jwt"


def rotate_field(client: hvac.Client, path: str, field: str) -> str:
    value = secrets.token_urlsafe(32)
    secret = client.secrets.kv.v2.read_secret_version(path=path)["data"]["data"]
    secret[field] = value
    client.secrets.kv.v2.create_or_update_secret(path=path, secret=secret)
    return value


def main() -> None:
    addr = os.environ["VAULT_ADDR"]
    token = os.environ["VAULT_TOKEN"]
    client = hvac.Client(url=addr, token=token)
    db = rotate_field(client, DB_PATH, "password")
    jwt = rotate_field(client, JWT_PATH, "secret")
    print("rotated DB and JWT secrets")
    print("DB_PASSWORD=", db)
    print("JWT_SECRET=", jwt)


if __name__ == "__main__":
    main()
