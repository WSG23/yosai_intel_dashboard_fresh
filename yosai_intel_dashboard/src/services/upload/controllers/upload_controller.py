from __future__ import annotations

import base64
import io
import json
import logging
from typing import Any, List, Optional

import pandas as pd

from validation.security_validator import SecurityValidator

logger = logging.getLogger(__name__)


class UnifiedUploadController:
    """Handle core upload parsing logic independent of Dash."""

    def __init__(self, validator: SecurityValidator | None = None) -> None:
        self._progress = 0
        self._files: List[str] = []
        self._validator = validator or SecurityValidator()

    def parse_upload(
        self, contents: str, filename: str, user: Any | None = None
    ) -> Optional[pd.DataFrame]:
        """Return parsed DataFrame from uploaded *contents*."""
        if not contents or not filename:
            return None

        if user is not None:
            self._validator.validate_resource_access(user, filename)

        try:
            _type, content_string = contents.split(",", 1)
            decoded = base64.b64decode(content_string)
            if filename.lower().endswith(".json"):
                data = json.loads(decoded.decode("utf-8"))
                df = pd.DataFrame(data)
            else:
                df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        except Exception as exc:  # pragma: no cover - parsing errors
            logger.error("Failed to parse uploaded file: %s", exc)
            return None

        return df
