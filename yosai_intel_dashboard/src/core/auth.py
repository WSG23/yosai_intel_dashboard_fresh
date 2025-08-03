from __future__ import annotations

"""Auth0 OIDC integration.

User model leverages mixins; see ADR-0005 for details.
"""

import json
import logging
import os
import socket
import time
from datetime import timedelta
from functools import wraps
from typing import List, Optional
from urllib.error import URLError
from urllib.request import urlopen

from authlib.integrations.flask_client import OAuth
from flask import Blueprint, current_app, redirect, session, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    login_required,
    login_user,
    logout_user,
)
from jose import jwt

from yosai_intel_dashboard.src.infrastructure.config import (
    get_cache_config,
    get_security_config,
)

from .secret_manager import SecretsManager

auth_bp = Blueprint("auth", __name__)
login_manager = LoginManager()
oauth = OAuth()
logger = logging.getLogger(__name__)


class User(UserMixin):
    def __init__(self, user_id: str, name: str, email: str, roles: List[str]):
        self.id = user_id
        self.name = name
        self.email = email
        self.roles = roles


_users: dict[str, User] = {}

# Cached JWKS per domain: {domain: (jwks_dict, fetch_timestamp)}
_jwks_cache: dict[str, tuple[dict, float]] = {}


@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    return _users.get(user_id)


@login_manager.request_loader
def load_user_from_request(request):
    user_id = session.get("user_id")
    if user_id:
        return _users.get(user_id)
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
        logger.warning(f"Failed to fetch JWKS from {jwks_url}: {exc}")
        if cached:
            return cached[0]
        raise
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
    return auth0.authorize_redirect(
        redirect_uri=url_for("auth.callback", _external=True),
        audience=current_app.config.get("AUTH0_AUDIENCE"),
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
    token = auth0.authorize_access_token()
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
    _users[user.id] = user
    login_user(user)
    _apply_session_timeout(user)
    session["roles"] = user.roles
    session["user_id"] = user.id
    return redirect("/")


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
    logout_user()
    session.clear()
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
                except Exception:
                    return "Forbidden", 403
            return func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = [
    "init_auth",
    "login_required",
    "role_required",
    "User",
    "login_manager",
]
