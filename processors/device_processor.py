from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from mapping.core.interfaces import ProcessorInterface


class DeviceProcessor(ProcessorInterface):
    """Extract device information from uploaded data."""

    def process(self, df: pd.DataFrame, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        column = "door_id" if "door_id" in df.columns else None
        devices = sorted(df[column].dropna().unique().tolist()) if column else []
        return {"devices": devices}
