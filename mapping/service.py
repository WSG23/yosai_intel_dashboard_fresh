from __future__ import annotations

import logging

import pandas as pd

from mapping.core.interfaces import ProcessorInterface, StorageInterface
from mapping.core.models import MappingData

logger = logging.getLogger(__name__)


class MappingService:
    """Coordinate processors and persistence."""

    def __init__(
        self,
        storage: StorageInterface,
        column_proc: ProcessorInterface,
        device_proc: ProcessorInterface,
    ) -> None:
        self.storage = storage
        self.column_proc = column_proc
        self.device_proc = device_proc

    def process_upload(self, df: pd.DataFrame, filename: str) -> MappingData:
        try:
            column_result = self.column_proc.process(df, filename)
            device_result = self.device_proc.process(column_result.data)
            return MappingData(columns=column_result, devices=device_result)
        except Exception as exc:  # pragma: no cover - logging only
            logger.exception("Failed to process upload: %s", exc)
            raise
