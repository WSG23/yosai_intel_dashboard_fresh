from flask import abort, current_app, request, session
from itsdangerous import URLSafeTimedSerializer


class CSRFProtect:
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.before_request(self._check_csrf)

    def _check_csrf(self):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            token = request.headers.get("X-CSRFToken") or request.form.get("csrf_token")
            try:
                validate_csrf(token)
            except Exception:
                abort(400)


def _serializer():
    secret = current_app.config.get("SECRET_KEY", "secret")
    return URLSafeTimedSerializer(secret)


def generate_csrf():
    token = _serializer().dumps("csrf")
    session["_csrf_token"] = token
    return token


def validate_csrf(token):
    if not token:
        raise ValueError("Missing CSRF token")
    _serializer().loads(token, max_age=3600)
    if session.get("_csrf_token") != token:
        raise ValueError("Invalid CSRF token")
