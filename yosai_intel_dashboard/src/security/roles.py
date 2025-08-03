"""Role based access control models and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from typing import Callable, Dict, List, Set

from flask import abort, session


@dataclass(frozen=True)
class Role:
    name: str
    permissions: Set[str]


ROLES: Dict[str, Role] = {
    "admin": Role("admin", {"admin:read", "admin:write"}),
    "user": Role("user", {"dashboard:view"}),
}


def get_permissions_for_roles(role_names: List[str]) -> Set[str]:
    perms: Set[str] = set()
    for name in role_names:
        role = ROLES.get(name)
        if role:
            perms |= role.permissions
    return perms


def require_roles(*required: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            roles = set(session.get("roles", []))
            if not roles.intersection(required):
                abort(403)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_permission(permission: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            perms = set(session.get("permissions", []))
            if permission not in perms:
                abort(403)
            return func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = [
    "Role",
    "ROLES",
    "get_permissions_for_roles",
    "require_roles",
    "require_permission",
]
