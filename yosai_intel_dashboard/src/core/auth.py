from __future__ import annotations

"""Auth0 OIDC integration.

User model leverages mixins; see ADR-0005 for details.
"""

import base64
import hashlib
import json
import logging
import os
import secrets
import socket
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import List, Optional
from urllib.error import URLError
from urllib.request import urlopen

import pyotp
from authlib.integrations.flask_client import OAuth
from flask import Blueprint, current_app, jsonify, redirect, request, session, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from jose import jwt

from yosai_intel_dashboard.src.infrastructure.config import (
    get_cache_config,
    get_security_config,
)
from yosai_intel_dashboard.src.security.roles import get_permissions_for_roles

from src.exceptions import AuthError, ExternalServiceError
from .secret_manager import SecretsManager
from .session_store import InMemorySessionStore, MemcachedSessionStore

auth_bp = Blueprint("auth", __name__)
login_manager = LoginManager()
oauth = OAuth()
logger = logging.getLogger(__name__)


@auth_bp.errorhandler(AuthError)
def handle_auth_error(err: AuthError):
    logger.warning("Authentication error", extra={"error": str(err)})
    return "Forbidden", 403


class User(UserMixin):
    def __init__(self, user_id: str, name: str, email: str, roles: List[str]):
        self.id = user_id
        self.name = name
        self.email = email
        self.roles = roles


session_store: MemcachedSessionStore | InMemorySessionStore = MemcachedSessionStore()

# Cached JWKS per domain: {domain: (jwks_dict, fetch_timestamp)}
_jwks_cache: dict[str, tuple[dict, float]] = {}


@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    data = session_store.get(user_id)
    if data is None:
        return None
    return User(
        data["id"], data.get("name", ""), data.get("email", ""), data.get("roles", [])
    )


@login_manager.request_loader
def load_user_from_request(request):
    user_id = session.get("user_id")
    if user_id:
        return load_user(user_id)
    return None


def init_auth(app) -> None:
    manager = SecretsManager()
    client_id = manager.get("AUTH0_CLIENT_ID")
    client_secret = manager.get("AUTH0_CLIENT_SECRET")
    domain = manager.get("AUTH0_DOMAIN")
    audience = manager.get("AUTH0_AUDIENCE")

    oauth.init_app(app)
    auth0 = oauth.register(
        "auth0",
        client_id=client_id,
        client_secret=client_secret,
        client_kwargs={"scope": "openid profile email"},
        server_metadata_url=f"https://{domain}/.well-known/openid-configuration",
    )

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    app.config.setdefault("AUTH0_AUDIENCE", audience)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE="Strict",
    )
    auth_bp.auth0 = auth0
    app.register_blueprint(auth_bp)


def _get_jwks(domain: str) -> dict:
    """Return cached JWKS for a domain if within TTL, otherwise fetch."""
    ttl = get_cache_config().jwks_ttl
    now = time.time()
    cached = _jwks_cache.get(domain)
    if cached and now - cached[1] < ttl:
        return cached[0]

    jwks_url = f"https://{domain}/.well-known/jwks.json"
    timeout = int(os.getenv("JWKS_TIMEOUT", "5"))
    try:
        with urlopen(jwks_url, timeout=timeout) as resp:
            jwks = json.load(resp)
    except (URLError, socket.timeout) as exc:
        logger.error(
            "Failed to fetch JWKS",
            extra={"url": jwks_url, "error": str(exc)},
        )
        if cached:
            return cached[0]
        raise ExternalServiceError("jwks_fetch_failed") from exc
    _jwks_cache[domain] = (jwks, now)
    return jwks


def _decode_jwt(token: str, domain: str, audience: str, client_id: str) -> dict:
    jwks = _get_jwks(domain)
    header = jwt.get_unverified_header(token)
    key = None
    for jwk in jwks["keys"]:
        if jwk["kid"] == header["kid"]:
            key = jwk
            break
    if key is None:
        raise ValueError("Public key not found")
    return jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        audience=audience or client_id,
        issuer=f"https://{domain}/",
    )


def _determine_session_timeout(roles: List[str]) -> int:
    """Return configured session timeout in seconds for given roles."""
    cfg = get_security_config()
    overrides = [
        cfg.session_timeout_by_role[r]
        for r in roles
        if r in cfg.session_timeout_by_role
    ]
    if overrides:
        return max(overrides)
    return cfg.session_timeout


def _apply_session_timeout(user: User) -> None:
    """Set session permanence and lifetime for the logged in user."""
    secs = _determine_session_timeout(user.roles)
    session.permanent = True
    current_app.permanent_session_lifetime = timedelta(seconds=secs)


@auth_bp.route("/login")
def login():
    """Begin OAuth login flow.
    ---
    get:
      description: Redirect user to Auth0 login
      responses:
        302:
          description: Redirect to Auth0
    """
    auth0 = auth_bp.auth0
    verifier = base64.urlsafe_b64encode(os.urandom(40)).rstrip(b"=").decode()
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    session["code_verifier"] = verifier
    return auth0.authorize_redirect(
        redirect_uri=url_for("auth.callback", _external=True),
        audience=current_app.config.get("AUTH0_AUDIENCE"),
        code_challenge=challenge,
        code_challenge_method="S256",
    )


@auth_bp.route("/callback")
def callback():
    """Handle OAuth provider callback.
    ---
    get:
      description: Process login response and sign in user
      responses:
        302:
          description: Redirect to dashboard
    """
    auth0 = auth_bp.auth0
    token = auth0.authorize_access_token(
        code_verifier=session.pop("code_verifier", None)
    )
    id_token = token.get("id_token")
    manager = SecretsManager()
    domain = manager.get("AUTH0_DOMAIN")
    audience = manager.get("AUTH0_AUDIENCE")
    client_id = manager.get("AUTH0_CLIENT_ID")
    claims = _decode_jwt(id_token, domain, audience, client_id)
    user = User(
        claims["sub"],
        claims.get("name", ""),
        claims.get("email", ""),
        claims.get("https://yosai-intel.io/roles", []),
    )
    login_user(user)
    _apply_session_timeout(user)
    ttl = _determine_session_timeout(user.roles)
    session_store.set(
        user.id,
        {"id": user.id, "name": user.name, "email": user.email, "roles": user.roles},
        ttl=ttl,
    )
    session["roles"] = user.roles
    session["user_id"] = user.id
    permissions = list(get_permissions_for_roles(user.roles))
    session["permissions"] = permissions
    secret = manager.get("JWT_SECRET")
    now = datetime.utcnow()
    access_token = jwt.encode(
        {
            "sub": user.id,
            "exp": now + timedelta(minutes=5),
            "roles": user.roles,
            "iat": now,
            "jti": secrets.token_urlsafe(8),
        },
        secret,
        algorithm="HS256",
    )
    refresh_token = jwt.encode(
        {
            "sub": user.id,
            "exp": now + timedelta(hours=1),
            "type": "refresh",
            "iat": now,
        },
        secret,
        algorithm="HS256",
    )
    session["access_token"] = access_token
    session["refresh_token"] = refresh_token
    if "admin" in user.roles:
        session["mfa_verified"] = False
    return redirect("/")


@auth_bp.route("/token")
@login_required
def token():
    return jsonify({"access_token": session.get("access_token")})


@auth_bp.route("/refresh")
@login_required
def refresh():
    manager = SecretsManager()
    secret = manager.get("JWT_SECRET")
    refresh_token = session.get("refresh_token")
    try:
        data = jwt.decode(refresh_token, secret, algorithms=["HS256"])
    except jwt.JWTError as err:
        logger.warning("Invalid refresh token", extra={"error": str(err)})
        raise AuthError("invalid_refresh_token") from err
    if data.get("type") != "refresh":
        raise AuthError("invalid_token_type")
    now = datetime.utcnow()
    new_access = jwt.encode(
        {
            "sub": data["sub"],
            "exp": now + timedelta(minutes=5),
            "roles": session.get("roles", []),
            "iat": now,
            "jti": secrets.token_urlsafe(8),
        },
        secret,
        algorithm="HS256",
    )
    session["access_token"] = new_access
    return jsonify({"access_token": new_access})


@auth_bp.route("/mfa")
@login_required
def mfa():
    return "MFA required", 200


@auth_bp.route("/mfa/verify")
@login_required
def mfa_verify():
    code = request.args.get("code")
    manager = SecretsManager()
    secret = manager.get("MFA_SECRET")
    totp = pyotp.TOTP(secret)
    if totp.verify(code):
        session["mfa_verified"] = True
        return redirect("/")
    return "Forbidden", 403


@auth_bp.route("/logout")
@login_required
def logout():
    """Log the user out.
    ---
    get:
      description: Terminate session and redirect
      responses:
        302:
          description: Redirect to login page
    """
    manager = SecretsManager()
    domain = manager.get("AUTH0_DOMAIN")
    user_id = session.get("user_id")
    logout_user()
    session.clear()
    if user_id:
        session_store.delete(user_id)
    return redirect(
        f"https://{domain}/v2/logout?returnTo="
        f"{url_for('auth.login', _external=True)}"
    )


def role_required(role: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            roles = session.get("roles", [])
            if role not in roles:
                try:
                    from dash.exceptions import PreventUpdate

                    raise PreventUpdate
                except ImportError:
                    return "Forbidden", 403
            return func(*args, **kwargs)

        return wrapper

    return decorator


def mfa_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("mfa_verified"):
            return redirect(url_for("auth.mfa"))
        return func(*args, **kwargs)

    return wrapper


__all__ = [
    "init_auth",
    "login_required",
    "role_required",
    "mfa_required",
    "User",
    "login_manager",
]
