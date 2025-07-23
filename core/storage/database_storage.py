"""In-memory database style storage service."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from core.base_model import BaseModel

from .protocols import DatabaseStorageProtocol


class DatabaseStorageService(BaseModel, DatabaseStorageProtocol):
    """Simple dictionary based record storage."""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self._tables: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._counter = 0

    def store_record(self, table: str, data: Dict[str, Any]) -> str:
        self._counter += 1
        record_id = str(self._counter)
        self._tables.setdefault(table, {})[record_id] = dict(data)
        return record_id

    def retrieve_record(self, table: str, record_id: str) -> Dict[str, Any]:
        return self._tables.get(table, {}).get(record_id, {})

    def update_record(
        self, table: str, record_id: str, updates: Dict[str, Any]
    ) -> bool:
        table_dict = self._tables.get(table, {})
        if record_id in table_dict:
            table_dict[record_id].update(updates)
            return True
        return False
