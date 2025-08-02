"""Rotate critical secrets stored in Vault."""

from __future__ import annotations

import logging
import os
import secrets
from typing import Iterable

from optional_dependencies import import_optional

hvac = import_optional("hvac")
requests = import_optional("requests")

DB_PATH = "secret/data/db"
JWT_PATH = "secret/data/jwt"


def rotate_field(client: hvac.Client, path: str, field: str) -> str:
    value = secrets.token_urlsafe(32)
    secret = client.secrets.kv.v2.read_secret_version(path=path)["data"]["data"]
    secret[field] = value
    client.secrets.kv.v2.create_or_update_secret(path=path, secret=secret)
    return value


def _notify_services(urls: Iterable[str]) -> None:
    """POST to `/invalidate-secret` on each base URL."""
    if not requests:
        logging.warning("requests library not available; skipping notifications")
        return
    for url in urls:
        url = url.rstrip("/") + "/invalidate-secret"
        try:
            requests.post(url, timeout=5)
        except Exception as exc:  # pragma: no cover - best effort
            logging.warning("failed to notify %s: %s", url, exc)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    if not hvac:
        raise RuntimeError("hvac library required to rotate secrets")
    addr = os.environ["VAULT_ADDR"]
    token = os.environ["VAULT_TOKEN"]
    client = hvac.Client(url=addr, token=token)
    rotate_field(client, DB_PATH, "password")
    rotate_field(client, JWT_PATH, "secret")
    logging.info("rotated DB and JWT secrets in Vault")

    urls = os.getenv("SECRET_INVALIDATE_URLS")
    if urls:
        _notify_services(u.strip() for u in urls.split(",") if u.strip())


if __name__ == "__main__":
    main()
