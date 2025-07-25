import time
from jose import jwt

from services.common.secrets import get_secret

SERVICE_JWT_SECRET = get_secret("secret/data/jwt#secret")


def generate_service_jwt(service_name: str, expires_in: int = 300) -> str:
    """Return a signed JWT token identifying ``service_name``."""
    now = int(time.time())
    payload = {"iss": service_name, "iat": now, "exp": now + expires_in}
    return jwt.encode(payload, SERVICE_JWT_SECRET, algorithm="HS256")


def verify_service_jwt(token: str) -> dict | None:
    """Verify a service JWT and return claims or ``None`` if invalid."""
    try:
        claims = jwt.decode(token, SERVICE_JWT_SECRET, algorithms=["HS256"])
    except Exception:
        return None
    exp = claims.get("exp")
    if exp is not None and exp < time.time():
        return None
    return claims
