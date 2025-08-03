from __future__ import annotations

import base64
import hashlib
import hmac
import time
from typing import Any, Dict

HEADER_SIGNATURE = "X-Signature"
HEADER_TIMESTAMP = "X-Signature-Timestamp"


def _canonical_string(method: str, path: str, body: bytes, timestamp: str) -> bytes:
    return b"\n".join([
        method.upper().encode(),
        path.encode(),
        timestamp.encode(),
        hashlib.sha256(body).hexdigest().encode(),
    ])


def sign_request(secret: str | bytes, method: str, path: str, body: bytes) -> Dict[str, str]:
    """Return headers containing an HMAC signature for the request."""
    if isinstance(secret, str):
        secret_bytes = secret.encode()
    else:
        secret_bytes = secret
    timestamp = str(int(time.time()))
    msg = _canonical_string(method, path, body, timestamp)
    sig = hmac.new(secret_bytes, msg, hashlib.sha256).digest()
    b64 = base64.b64encode(sig).decode()
    return {HEADER_SIGNATURE: b64, HEADER_TIMESTAMP: timestamp}


def verify_request(secret: str | bytes, method: str, path: str, body: bytes, headers: Dict[str, str], max_skew: int = 300) -> bool:
    """Verify HMAC signature from ``headers``.

    ``max_skew`` specifies the maximum allowed clock skew in seconds.
    """
    signature = headers.get(HEADER_SIGNATURE)
    timestamp = headers.get(HEADER_TIMESTAMP)
    if not signature or not timestamp:
        return False
    if abs(int(time.time()) - int(timestamp)) > max_skew:
        return False
    expected = sign_request(secret, method, path, body)
    return hmac.compare_digest(signature, expected[HEADER_SIGNATURE])
