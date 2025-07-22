from flask import jsonify
from typing import Any, Optional

def error_response(code: str, message: str, details: Optional[Any] = None):
    body = {"code": code, "message": message}
    if details is not None:
        body["details"] = details
    return jsonify(body)
