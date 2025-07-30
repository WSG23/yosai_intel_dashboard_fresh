from __future__ import annotations

"""Processing helpers for the data enhancer page."""

import base64
import io
import json
import logging
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from .mapping_utils import get_ai_column_suggestions

logger = logging.getLogger(__name__)


class DataEnhancerProcessor:
    """Utility class for transforming uploaded files."""

    # ------------------------------------------------------------------
    def decode_contents(
        self, contents: str, filename: str
    ) -> Tuple[Optional[pd.DataFrame], str]:
        """Return dataframe decoded from ``contents`` with status message."""
        try:
            _ctype, content_string = contents.split(",", 1)
            decoded = base64.b64decode(content_string)
            if filename.lower().endswith(".csv"):
                df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
            elif filename.lower().endswith(".json"):
                data = json.loads(decoded.decode("utf-8"))
                df = (
                    pd.json_normalize(data)
                    if isinstance(data, list)
                    else pd.DataFrame([data])
                )
            else:
                return None, f"Unsupported file type: {filename}"
            return df, f"Loaded {filename}"
        except Exception as exc:  # pragma: no cover - best effort
            logger.error("Decoding failed for %s: %s", filename, exc)
            return None, f"Failed to read {filename}"

    # ------------------------------------------------------------------
    def get_column_suggestions(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Return heuristic column suggestions for ``df``."""
        ai = get_ai_column_suggestions(list(df.columns))
        suggestions: Dict[str, Dict[str, Any]] = {}
        for col, info in ai.items():
            field = info.get("field")
            if field:
                current = suggestions.get(field)
                if not current or info["confidence"] > current.get("confidence", 0):
                    suggestions[field] = {
                        "suggested_column": col,
                        "confidence": info.get("confidence", 0),
                    }
        return suggestions

    # ------------------------------------------------------------------
    def apply_column_mappings(
        self, df: pd.DataFrame, mappings: Dict[str, str]
    ) -> pd.DataFrame:
        """Rename columns in ``df`` according to ``mappings``."""
        rename = {v: k for k, v in mappings.items() if v}
        return df.rename(columns=rename)


__all__ = ["DataEnhancerProcessor"]
