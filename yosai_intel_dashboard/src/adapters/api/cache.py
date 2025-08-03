import hashlib
import json
import time
from email.utils import formatdate
from fastapi.responses import JSONResponse


def cached_json_response(data: dict, max_age: int = 3600) -> JSONResponse:
    """Return a JSON response with caching headers.

    Adds ``ETag``, ``Cache-Control``, and ``Expires`` headers so clients can
    cache responses for ``max_age`` seconds.
    """
    body = json.dumps(data, sort_keys=True).encode("utf-8")
    etag = hashlib.sha1(body).hexdigest()
    expires = formatdate(time.time() + max_age, usegmt=True)
    response = JSONResponse(content=data)
    response.headers["ETag"] = f'"{etag}"'
    response.headers["Cache-Control"] = f"public, max-age={max_age}"
    response.headers["Expires"] = expires
    return response
