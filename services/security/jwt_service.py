import time
from jose import jwt

from services.common.secrets import get_secret

_SECRET_PATH = "secret/data/jwt#secret"


def _jwt_secret() -> str:
    """Return the current JWT secret from Vault."""
    return get_secret(_SECRET_PATH)


def generate_service_jwt(service_name: str, expires_in: int = 300) -> str:
    """Return a signed JWT token identifying ``service_name``."""
    now = int(time.time())
    payload = {"iss": service_name, "iat": now, "exp": now + expires_in}
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


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
