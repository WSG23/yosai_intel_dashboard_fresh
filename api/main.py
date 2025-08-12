from fastapi import FastAPI
from api.middleware.body_size_limit import BodySizeLimitMiddleware
from api.middleware.security_headers import SecurityHeadersMiddleware

app = FastAPI()
app.add_middleware(BodySizeLimitMiddleware, max_bytes=50 * 1024 * 1024)
app.add_middleware(SecurityHeadersMiddleware)
