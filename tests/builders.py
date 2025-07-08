from __future__ import annotations

import os

from typing import Any, Dict

import pandas as pd

from config.complete_service_registration import register_all_services
from core.service_container import ServiceContainer
from core.protocols import UnicodeProcessorProtocol
from services.upload.protocols import UploadStorageProtocol
from tests.test_doubles import InMemoryUploadStore, SimpleUnicodeProcessor


class TestContainerBuilder:
    """Helper for constructing ServiceContainer instances for tests."""


    def __init__(self) -> None:
        self._container = ServiceContainer()

    # ------------------------------------------------------------------
    def with_env_defaults(self) -> "TestContainerBuilder":
        """Retained for backward compatibility (no-op)."""
        return self

    # ------------------------------------------------------------------
    def with_all_services(self) -> "TestContainerBuilder":
        register_all_services(self._container)
        return self

    # ------------------------------------------------------------------
    def with_unicode_processor(self) -> "TestContainerBuilder":
        self._container.register_singleton(
            "unicode_processor",
            SimpleUnicodeProcessor,
            protocol=UnicodeProcessorProtocol,
        )
        return self

    # ------------------------------------------------------------------
    def with_upload_store(self) -> "TestContainerBuilder":
        store = InMemoryUploadStore()
        self._container.register_singleton(
            "upload_storage",
            lambda: store,
            protocol=UploadStorageProtocol,
        )
        return self

    # ------------------------------------------------------------------
    def build(self) -> ServiceContainer:
        return self._container


class TestDataBuilder:
    """Utility for constructing sample analytics dataframes."""

    def __init__(self) -> None:
        self._rows: list[Dict[str, Any]] = []

    def add_row(
        self,
        *,
        timestamp: str = "2024-01-01 00:00:00",
        person_id: str = "u1",
        token_id: str = "t1",
        door_id: str = "d1",
        access_result: str = "Granted",
    ) -> "TestDataBuilder":
        self._rows.append(
            {
                "timestamp": pd.to_datetime(timestamp),
                "person_id": person_id,
                "token_id": token_id,
                "door_id": door_id,
                "access_result": access_result,
            }
        )
        return self

    def build_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self._rows)

    def as_upload_dict(self, filename: str = "sample.csv") -> Dict[str, pd.DataFrame]:
        return {filename: self.build_dataframe()}
