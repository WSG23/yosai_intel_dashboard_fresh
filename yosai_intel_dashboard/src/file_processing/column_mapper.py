from __future__ import annotations

from typing import Dict, Iterable, List, Optional

import pandas as pd
from rapidfuzz import process

from yosai_intel_dashboard.src.infrastructure.callbacks.events import CallbackEvent
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks

REQUIRED_COLUMNS = ["person_id", "door_id", "access_result", "timestamp"]
OPTIONAL_COLUMNS = ["device_name", "location"]


def map_columns(
    df: pd.DataFrame,
    canonical_names: Dict[str, Iterable[str]],
    *,
    fuzzy_threshold: int = 80,
    controller: Optional[TrulyUnifiedCallbacks] = None,
) -> pd.DataFrame:
    """Rename columns in ``df`` using provided mapping rules."""
    controller = controller or TrulyUnifiedCallbacks()
    df_out = df.copy()
    reverse: Dict[str, str] = {}
    for canon, aliases in canonical_names.items():
        reverse[canon.lower()] = canon
        for alias in aliases:
            reverse[alias.lower()] = canon

    renamed = {}
    for col in df_out.columns:
        target = reverse.get(str(col).lower())
        if target:
            renamed[col] = target
    if renamed:
        df_out = df_out.rename(columns=renamed)

    unmapped = set(df_out.columns) - set(canonical_names)
    choices = REQUIRED_COLUMNS + OPTIONAL_COLUMNS
    for col in unmapped:
        best = process.extractOne(str(col), choices)
        if best and best[1] >= fuzzy_threshold:
            df_out = df_out.rename(columns={col: best[0]})
        else:
            suggestions = process.extract(str(col), choices, limit=3)
            controller.trigger(
                CallbackEvent.SYSTEM_WARNING,
                "column_mapper",
                {
                    "warning": "MappingWarning",
                    "column": col,
                    "suggestions": [s[0] for s in suggestions],
                },
            )
    return df_out
