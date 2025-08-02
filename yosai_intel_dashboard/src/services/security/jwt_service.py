from __future__ import annotations

import time

from jose import jwt

from yosai_intel_dashboard.src.services.common.secrets import (
    get_secret,
    invalidate_secret,
)

_SECRET_PATH = "secret/data/jwt#secret"
_JWT_SECRET_TTL = 300  # seconds

_cached_secret: str | None = None
_cache_expires_at: float = 0.0


def _read_jwt_secret() -> str:
    """Read the current JWT secret from Vault."""
    return get_secret(_SECRET_PATH)


def jwt_secret() -> str:
    """Return the cached JWT secret, refreshing it as needed."""
    global _cached_secret, _cache_expires_at
    now = time.time()
    if _cached_secret is None or now >= _cache_expires_at:
        _cached_secret = _read_jwt_secret()
        _cache_expires_at = now + _JWT_SECRET_TTL if _JWT_SECRET_TTL else float("inf")
    return _cached_secret


def invalidate_jwt_secret_cache() -> None:
    """Invalidate the cached JWT secret."""
    global _cached_secret, _cache_expires_at
    _cached_secret = None
    _cache_expires_at = 0.0
    invalidate_secret(_SECRET_PATH)


def generate_service_jwt(service_name: str, expires_in: int = 300) -> str:
    """Return a signed JWT token identifying ``service_name``."""
    now = int(time.time())
    payload = {"iss": service_name, "iat": now, "exp": now + expires_in}
    return jwt.encode(payload, jwt_secret(), algorithm="HS256")


def generate_refresh_jwt(service_name: str, expires_in: int = 3600) -> str:
    """Return a signed refresh JWT token identifying ``service_name``."""
    now = int(time.time())
    payload = {
        "iss": service_name,
        "iat": now,
        "exp": now + expires_in,
        "typ": "refresh",
    }
    return jwt.encode(payload, jwt_secret(), algorithm="HS256")


def generate_token_pair(
    service_name: str,
    access_expires_in: int = 300,
    refresh_expires_in: int = 3600,
) -> tuple[str, str]:
    """Return an ``(access, refresh)`` token pair."""
    return (
        generate_service_jwt(service_name, access_expires_in),
        generate_refresh_jwt(service_name, refresh_expires_in),
    )


def verify_service_jwt(token: str) -> dict | None:
    """Verify a service JWT and return claims or ``None`` if invalid."""
    try:
        claims = jwt.decode(token, jwt_secret(), algorithms=["HS256"])
    except Exception:
        return None
    exp = claims.get("exp")
    if exp is not None and exp < time.time():
        return None
    return claims


def verify_refresh_jwt(token: str) -> dict | None:
    """Verify a refresh JWT and return claims or ``None`` if invalid."""
    claims = verify_service_jwt(token)
    if not claims or claims.get("typ") != "refresh":
        return None
    return claims


def refresh_access_token(refresh_token: str, expires_in: int = 300) -> str | None:
    """Return a new access token if ``refresh_token`` is valid."""
    claims = verify_refresh_jwt(refresh_token)
    if not claims:
        return None
    return generate_service_jwt(claims["iss"], expires_in)
