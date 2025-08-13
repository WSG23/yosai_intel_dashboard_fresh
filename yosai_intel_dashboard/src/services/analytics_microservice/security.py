"""Local security helpers used for testing.

These implementations are intentionally lightweight. They provide just enough
functionality for the analytics microservice during tests while mimicking the
behaviour of the real security module.  When the real implementations are
available they should be preferred instead of these stubs.
"""

from __future__ import annotations

import os
from typing import Any, Callable

from fastapi import Header, HTTPException
from jose import jwt

from yosai_intel_dashboard.src.services.common import secrets


def rate_limit_decorator(
    *_args, **_kwargs
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Fallback rate limit decorator used only when the real one is absent.

    The decorator returned simply calls the wrapped function without imposing
    any rate limiting.  It mirrors the signature of the actual decorator so
    that calling code does not need to change when the real implementation is
    present.
    """

    def _decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return func

    return _decorator


def verify_token(authorization: str = Header("")) -> dict:
    """Validate a bearer token using the configured JWT secret.

    Parameters
    ----------
    authorization:
        The ``Authorization`` header provided with the request.

    Returns
    -------
    dict
        The decoded JWT payload.

    Raises
    ------
    HTTPException
        If the header is missing/invalid or the token cannot be decoded.
    """

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="invalid authorization header")

    token = authorization.split(" ", 1)[1]
    secret = secrets.get_secret("JWT_SECRET_KEY") or os.getenv("JWT_SECRET_KEY", "")
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=401, detail="invalid token") from exc


__all__ = ["rate_limit_decorator", "verify_token"]
