import time

from jose import jwt

from yosai_intel_dashboard.src.services.common.secrets import get_secret

_SECRET_PATH = "secret/data/jwt#secret"


def _jwt_secret() -> str:
    """Return the current JWT secret from Vault."""
    return get_secret(_SECRET_PATH)


def generate_service_jwt(service_name: str, expires_in: int = 300) -> str:
    """Return a signed JWT token identifying ``service_name``."""
    now = int(time.time())
    payload = {"iss": service_name, "iat": now, "exp": now + expires_in}
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def generate_refresh_jwt(service_name: str, expires_in: int = 3600) -> str:
    """Return a signed refresh JWT token identifying ``service_name``."""
    now = int(time.time())
    payload = {
        "iss": service_name,
        "iat": now,
        "exp": now + expires_in,
        "typ": "refresh",
    }
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


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
        claims = jwt.decode(token, _jwt_secret(), algorithms=["HS256"])
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
