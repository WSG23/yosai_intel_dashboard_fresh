from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, Dict, List

import pandas as pd

from yosai_intel_dashboard.src.core.config import get_max_display_rows
from yosai_intel_dashboard.src.core.interfaces.protocols import ConfigurationProtocol
from yosai_intel_dashboard.src.core.unicode import sanitize_for_utf8

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
        dynamic_config,
    )

logger = logging.getLogger(__name__)


def serialize_dataframe_preview(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Return a JSON-safe preview of ``df`` for callbacks.

    The preview always uses ``df.head(5)`` and the DataFrame is first clamped to
    fewer than 100 rows. If the serialized preview exceeds 5MB, an empty list is
    returned.
    """
    try:
        limited_df = df.head(get_max_display_rows())

        preview = limited_df.head(5).to_dict("records")
        preview = [{k: sanitize_for_utf8(v) for k, v in row.items()} for row in preview]
        serialized = json.dumps(preview, ensure_ascii=False)
        if len(serialized.encode("utf-8")) >= 5 * 1024 * 1024:
            logger.warning("Serialized preview exceeds 5MB; omitting preview")
            return []
        return preview
    except Exception as exc:  # pragma: no cover - best effort
        logger.exception(f"Failed to serialize dataframe preview: {exc}")
        return []
