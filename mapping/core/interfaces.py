from __future__ import annotations

from abc import abstractmethod
from typing import Any, Dict, Protocol

import pandas as pd

from .models import ProcessingResult


class StorageInterface(Protocol):
    """Abstract persistence backend."""

    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """Return the stored mapping data."""
        ...

    @abstractmethod
    def save(self, data: Dict[str, Any]) -> None:
        """Persist mapping *data*."""
        ...


class ProcessorInterface(Protocol):
    """Transform raw uploaded data."""

    @abstractmethod
    def process(self, df: pd.DataFrame, *args: Any, **kwargs: Any) -> ProcessingResult:
        """Return processed representation of *df*."""
        ...


class LearningInterface(Protocol):
    """Provide learned mapping operations."""

    @abstractmethod
    def save_complete_mapping(
        self,
        df: pd.DataFrame,
        filename: str,
        device_mappings: Dict[str, Any],
        column_mappings: Dict[str, str] | None = None,
    ) -> str: ...

    @abstractmethod
    def get_learned_mappings(
        self, df: pd.DataFrame, filename: str
    ) -> Dict[str, Any]: ...

    @abstractmethod
    def apply_to_global_store(self, df: pd.DataFrame, filename: str) -> bool: ...
