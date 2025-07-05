import json
import logging
from typing import Any, List, Dict
import pandas as pd

from security.unicode_security_processor import sanitize_unicode_input

logger = logging.getLogger(__name__)


def serialize_dataframe_preview(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Return a JSON-safe preview of ``df`` for callbacks.

    The preview always uses ``df.head(5)`` and the DataFrame is first clamped to
    fewer than 100 rows. If the serialized preview exceeds 5MB, an empty list is
    returned.
    """
    try:
        limited_df = df.head(99)  # clamp DataFrame to <100 rows
        preview = limited_df.head(5).to_dict("records")
        preview = [
            {k: sanitize_unicode_input(v) for k, v in row.items()}
            for row in preview
        ]
        serialized = json.dumps(preview, ensure_ascii=False)
        if len(serialized.encode("utf-8")) >= 5 * 1024 * 1024:
            logger.warning("Serialized preview exceeds 5MB; omitting preview")
            return []
        return preview
    except Exception as exc:  # pragma: no cover - best effort
        logger.exception("Failed to serialize dataframe preview: %s", exc)
        return []
