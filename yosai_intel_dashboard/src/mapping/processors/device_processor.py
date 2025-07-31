from __future__ import annotations

from typing import Any

import pandas as pd

from mapping.core.interfaces import ProcessorInterface
from mapping.core.models import ProcessingResult


class DeviceProcessor(ProcessorInterface):
    """Extract device information from uploaded data."""

    def process(self, df: pd.DataFrame, *args: Any, **kwargs: Any) -> ProcessingResult:
        column = "door_id" if "door_id" in df.columns else None
        devices = sorted(df[column].dropna().unique().tolist()) if column else []
        return ProcessingResult(data=df, metadata={"devices": devices})
