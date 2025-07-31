from __future__ import annotations

"""Protocol definitions for data processing components."""

from typing import Any, Dict, Iterator, Protocol, Tuple, runtime_checkable

import pandas as pd


@runtime_checkable
class ProcessorProtocol(Protocol):
    """Interface for the :class:`Processor` data handler."""

    def load_dataframe(self, source: Any) -> pd.DataFrame:
        """Return a cleaned DataFrame for ``source``."""
        ...

    def stream_file(self, source: Any, chunksize: int = 1000) -> Iterator[pd.DataFrame]:
        """Yield processed chunks from ``source``."""
        ...

    def consume_stream(self, timeout: float = 1.0) -> Iterator[pd.DataFrame]:
        """Consume events from an attached streaming service."""
        ...

    def get_processed_database(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Return uploaded data combined with mapping metadata."""
        ...


__all__ = ["ProcessorProtocol"]

