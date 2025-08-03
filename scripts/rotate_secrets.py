#!/usr/bin/env python3
"""Rotate Kubernetes secrets for staging environments.

This script generates new secret values, writes them to the configured
secret backend and updates ``k8s/config/api-secrets.yaml`` with
references to those locations.
"""
from __future__ import annotations

import logging
import os
import secrets
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from optional_dependencies import import_optional

hvac = import_optional("hvac")
boto3 = import_optional("boto3")

SECRETS_FILE = Path("k8s/config/api-secrets.yaml")

# Mapping of secret names to backend locations
SECRET_SPECS = {
    "SECRET_KEY": {
        "vault": ("secret/data/api", "secret_key"),
        "aws": "prod/app_secret",
    },
    "DB_PASSWORD": {
        "vault": ("secret/data/db", "password"),
        "aws": "prod/db_password",
    },
    "TIMESCALE_DB_PASSWORD": {
        "vault": ("secret/data/timescale", "password"),
        "aws": "prod/timescale_db_password",
    },
}


def generate_token(length: int = 32) -> str:
    """Return a URL-safe random token."""
    return secrets.token_urlsafe(length)


def _get_vault_client() -> Optional[Any]:
    if not hvac:
        return None
    addr = os.getenv("VAULT_ADDR")
    token = os.getenv("VAULT_TOKEN")
    if not (addr and token):
        return None
    try:
        return hvac.Client(url=addr, token=token)
    except Exception:  # pragma: no cover - network/setup issues
        logging.exception("failed to initialise Vault client")
        return None


def _get_aws_client() -> Optional[Any]:
    if not boto3:
        return None
    region = os.getenv("AWS_REGION")
    if not region:
        return None
    try:
        return boto3.client("secretsmanager", region_name=region)
    except Exception:  # pragma: no cover - network/setup issues
        logging.exception("failed to initialise AWS client")
        return None


def _write_vault_secret(client: Any, path: str, field: str, value: str) -> str:
    client.secrets.kv.v2.create_or_update_secret(path=path, secret={field: value})
    return f"vault:{path}#{field}"


def _write_aws_secret(client: Any, name: str, value: str) -> str:
    try:
        client.put_secret_value(SecretId=name, SecretString=value)
    except getattr(client, "exceptions", object()).__dict__.get(
        "ResourceNotFoundException", Exception
    ):
        client.create_secret(Name=name, SecretString=value)
    return f"aws-secrets:{name}"


def update_secrets(file_path: Path = SECRETS_FILE) -> Dict[str, str]:
    """Generate secrets, store them in the backend and update references."""
    data: Dict[str, Any] = yaml.safe_load(file_path.read_text())
    string_data = data.setdefault("stringData", {})

    vault_client = _get_vault_client()
    aws_client = _get_aws_client()
    backend = "vault" if vault_client else "aws" if aws_client else None
    if backend is None:
        raise RuntimeError("No secret backend configured")

    references: Dict[str, str] = {}
    for key, spec in SECRET_SPECS.items():
        if key == "TIMESCALE_DB_PASSWORD" and key not in string_data:
            continue
        value = generate_token()
        if backend == "vault":
            path, field = spec["vault"]
            ref = _write_vault_secret(vault_client, path, field, value)
        else:
            name = spec["aws"]
            ref = _write_aws_secret(aws_client, name, value)
        string_data[key] = ref
        references[key] = ref

    file_path.write_text(yaml.safe_dump(data))
    return references


def cluster_reachable() -> bool:
    """Return True if kubectl can reach a cluster."""
    try:
        subprocess.run(
            ["kubectl", "cluster-info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=10,
        )
        return True
    except Exception:
        return False


def apply_config(file_path: Path = SECRETS_FILE) -> None:
    """Apply the secret manifest using kubectl if possible."""
    if not cluster_reachable():
        logging.warning("kubectl not configured or cluster unreachable; skipping apply")
        return
    subprocess.run(["kubectl", "apply", "-f", str(file_path)], check=True)


def restart_deployment(
    deployment: str = "yosai-dashboard", namespace: str = "yosai-dev"
) -> None:
    """Trigger a rolling restart of the given deployment."""
    if not cluster_reachable():
        return
    subprocess.run(
        ["kubectl", "rollout", "restart", f"deployment/{deployment}", "-n", namespace],
        check=True,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    try:
        updates = update_secrets()
    except RuntimeError as exc:  # pragma: no cover - configuration issue
        logging.error("%s", exc)
        return
    logging.info("Secrets rotated and written to %s", SECRETS_FILE)
    for key, ref in updates.items():
        logging.info("rotated %s -> %s", key, ref)
    apply_config()
    restart_deployment()


if __name__ == "__main__":
    main()
