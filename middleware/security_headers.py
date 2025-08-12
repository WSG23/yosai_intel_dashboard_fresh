from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add common security headers to each response."""

    def __init__(self, app, csp: str | None = None) -> None:
        super().__init__(app)
        self.csp = csp or "default-src 'self'"
        self.hsts = "max-age=63072000; includeSubDomains; preload"
        self.frame_options = "DENY"
        self.content_type_options = "nosniff"
        self.referrer_policy = "no-referrer"
        self.permissions_policy = (
            "geolocation=(), camera=(), microphone=(), fullscreen=()"
        )

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers.setdefault("Content-Security-Policy", self.csp)
        response.headers.setdefault("Strict-Transport-Security", self.hsts)
        response.headers.setdefault("X-Frame-Options", self.frame_options)
        response.headers.setdefault("X-Content-Type-Options", self.content_type_options)
        response.headers.setdefault("Referrer-Policy", self.referrer_policy)
        response.headers.setdefault("Permissions-Policy", self.permissions_policy)
        return response
