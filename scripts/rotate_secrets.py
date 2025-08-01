#!/usr/bin/env python3
"""Rotate Kubernetes secrets for staging environments.

This script generates new SECRET_KEY and database password values,
updates ``k8s/config/api-secrets.yaml`` with those values and applies
the manifest with ``kubectl`` if the cluster is reachable.
"""
from __future__ import annotations

import logging
import secrets
import subprocess
from pathlib import Path
from typing import Any, Dict

import yaml

SECRETS_FILE = Path("k8s/config/api-secrets.yaml")


def generate_token(length: int = 32) -> str:
    """Return a URL-safe random token."""
    return secrets.token_urlsafe(length)


def update_secrets(file_path: Path = SECRETS_FILE) -> Dict[str, str]:
    """Update the secrets file with new credentials."""
    data: Dict[str, Any] = yaml.safe_load(file_path.read_text())
    string_data = data.setdefault("stringData", {})
    updates = {
        "SECRET_KEY": generate_token(),
        "DB_PASSWORD": generate_token(),
    }
    if "TIMESCALE_DB_PASSWORD" in string_data:
        updates["TIMESCALE_DB_PASSWORD"] = generate_token()
    string_data.update(updates)
    file_path.write_text(yaml.safe_dump(data))
    return updates


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
    updates = update_secrets()
    logging.info("Secrets rotated and written to %s", SECRETS_FILE)
    for key in updates:
        logging.info("rotated %s", key)
    apply_config()
    restart_deployment()


if __name__ == "__main__":
    main()
