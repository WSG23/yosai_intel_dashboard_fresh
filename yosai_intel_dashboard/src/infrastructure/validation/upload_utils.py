from __future__ import annotations

import base64
import os
from typing import Dict, List

from yosai_intel_dashboard.src.core.exceptions import ValidationError

from .security_validator import SecurityValidator


def decode_and_validate_upload(
    contents: str,
    filename: str,
    validator: SecurityValidator | None = None,
) -> Dict[str, any]:
    """Decode base64 ``contents`` and validate upload metadata.

    Returns a dict with keys ``valid``, ``filename``, ``decoded`` (bytes or ``None``),
    ``size_mb`` when valid and ``issues`` listing any problems.
    """
    validator = validator or SecurityValidator()
    issues: List[str] = []
    try:
        sanitized = validator.sanitize_filename(filename)
    except ValidationError:
        sanitized = os.path.basename(filename)
        issues.append("Invalid filename")

    if "," not in contents:
        issues.append("Invalid data URI")
        return {
            "valid": False,
            "filename": sanitized,
            "decoded": None,
            "issues": issues,
        }

    try:
        _, data = contents.split(",", 1)
        decoded = base64.b64decode(data, validate=True)
    except (base64.binascii.Error, ValueError) as exc:
        issues.append(f"Invalid base64 data: {exc}")
        return {
            "valid": False,
            "filename": sanitized,
            "decoded": None,
            "issues": issues,
        }

    res = validator.file_validator.validate_file_upload(sanitized, decoded)
    res.setdefault("issues", [])
    res["issues"] = issues + res["issues"]
    if res["valid"]:
        res["decoded"] = decoded
    else:
        res["decoded"] = None
    res["filename"] = sanitized
    return res
