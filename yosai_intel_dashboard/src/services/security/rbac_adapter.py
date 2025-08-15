"""Adapter exposing Go RBAC checks to Python."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re


@lru_cache()
def _permissions() -> dict[str, list[str]]:
    go_file = (
        Path(__file__).resolve().parents[4]
        / "services"
        / "gateway"
        / "auth"
        / "rbac.go"
    )
    text = go_file.read_text()
    pattern = re.compile(r'"([^"]+)":\s*{([^}]*)}', re.MULTILINE)
    perms: dict[str, list[str]] = {}
    for role, body in pattern.findall(text):
        perms[role] = [p.strip().strip('"') for p in body.split(",") if p.strip()]
    return perms


def has_permission(role: str, permission: str) -> bool:
    """Return ``True`` if *role* is allowed *permission* according to Go RBAC."""
    return permission in _permissions().get(role, [])


__all__ = ["has_permission"]
