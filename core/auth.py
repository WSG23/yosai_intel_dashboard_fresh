from __future__ import annotations

"""Auth0 OIDC integration"""

import json
import os
import time
from functools import wraps
from typing import Optional, List
from urllib.request import urlopen

from flask import Blueprint, redirect, url_for, session, current_app, request
from flask_login import (
    LoginManager,
    UserMixin,
    login_required,
    login_user,
    logout_user,
    current_user,
)
from authlib.integrations.flask_client import OAuth
from jose import jwt

from .secret_manager import SecretManager


auth_bp = Blueprint("auth", __name__)
login_manager = LoginManager()
oauth = OAuth()


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
    manager = SecretManager()
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
    ttl = int(os.getenv("JWKS_CACHE_TTL", "300"))
    now = time.time()
    cached = _jwks_cache.get(domain)
    if cached and now - cached[1] < ttl:
        return cached[0]

    jwks_url = f"https://{domain}/.well-known/jwks.json"
    with urlopen(jwks_url) as resp:
        jwks = json.load(resp)
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
    """Handle OAuth provider callback."""
    auth0 = auth_bp.auth0
    token = auth0.authorize_access_token()
    id_token = token.get("id_token")
    manager = SecretManager()
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
    manager = SecretManager()
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
