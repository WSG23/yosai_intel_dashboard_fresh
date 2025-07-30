import base64
import io
import json
import logging
from typing import List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class UnifiedUploadController:
    """Handle core upload parsing logic independent of Dash."""

    def __init__(self) -> None:
        self._progress = 0
        self._files: List[str] = []

    def parse_upload(self, contents: str, filename: str) -> Optional[pd.DataFrame]:
        """Return parsed DataFrame from uploaded *contents*."""
        if not contents or not filename:
            return None

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
