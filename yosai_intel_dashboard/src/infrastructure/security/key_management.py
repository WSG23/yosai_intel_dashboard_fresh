"""Key management utilities for secret rotation and derivation.

This module provides helper functions and classes to rotate secrets stored
in Vault or AWS Secrets Manager and to derive subkeys from a master key
using the HKDF algorithm as described in RFC 5869.  The implementation
only relies on the Python standard library so it works in minimal
environments.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol

try:  # optional dependencies for backends
    import hvac  # type: ignore
except Exception:  # pragma: no cover
    hvac = None

try:  # pragma: no cover
    import boto3  # type: ignore
except Exception:  # pragma: no cover
    boto3 = None


class SecretWriter(Protocol):  # pragma: no cover - interface definition
    def write(self, name: str, value: str) -> None:
        ...


def hkdf(master: bytes, *, salt: bytes, info: bytes = b"", length: int = 32) -> bytes:
    """Derive a new key from ``master`` using HKDF (SHA-256)."""

    if not salt:
        salt = b"\x00" * hashlib.sha256().digest_size
    prk = hmac.new(salt, master, hashlib.sha256).digest()
    t = b""
    okm = b""
    for i in range(1, -(-length // hashlib.sha256().digest_size) + 1):
        t = hmac.new(prk, t + info + bytes([i]), hashlib.sha256).digest()
        okm += t
    return okm[:length]


def _vault_writer(path: str):  # pragma: no cover - runtime helper
    if not hvac:
        raise RuntimeError("hvac is required for Vault operations")
    client = hvac.Client(url=os.getenv("VAULT_ADDR"), token=os.getenv("VAULT_TOKEN"))

    def _write(name: str, value: str) -> None:
        client.secrets.kv.v2.create_or_update_secret(path=path, secret={name: value})

    return _write


def _aws_writer(name: str):  # pragma: no cover - runtime helper
    if not boto3:
        raise RuntimeError("boto3 is required for AWS operations")
    client = boto3.client("secretsmanager", region_name=os.getenv("AWS_REGION"))

    def _write(key: str, value: str) -> None:
        client.put_secret_value(SecretId=name, SecretString=json.dumps({key: value}))

    return _write


@dataclass
class KeyManager:
    """Manage application keys and perform rotation when needed."""

    writer: SecretWriter
    rotation_days: int = 90

    def rotation_needed(self, last_rotated: datetime) -> bool:
        return datetime.utcnow() - last_rotated > timedelta(days=self.rotation_days)

    def rotate(self, name: str) -> str:
        """Generate and store a new key using the configured writer."""

        new_key = secrets.token_urlsafe(32)
        self.writer.write(name, new_key)
        return new_key

    @staticmethod
    def derive(master: bytes, *, context: bytes, length: int = 32) -> bytes:
        """Derive a context-specific key from ``master`` using HKDF."""

        return hkdf(master, salt=context, info=b"yosai-key", length=length)


__all__ = ["hkdf", "KeyManager", "_vault_writer", "_aws_writer"]

