import logging
from typing import IO, Any, List, Tuple, Union

import pandas as pd

logger = logging.getLogger(__name__)


class StreamProcessor:
    """Helper utilities for streaming data processing."""

    @staticmethod
    def process_large_csv(
        file_like: Union[str, IO[str]],
        *,
        chunk_size: int = 10000,
        **read_kwargs: Any,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Read ``file_like`` CSV in ``chunk_size`` pieces.

        Returns the concatenated DataFrame and a list of chunk error messages.
        """
        chunks: List[pd.DataFrame] = []
        errors: List[str] = []
        try:
            reader = pd.read_csv(file_like, chunksize=chunk_size, **read_kwargs)
        except Exception as exc:  # pragma: no cover - invalid CSV
            logger.error("Failed to create CSV reader: %s", exc)
            return pd.DataFrame(), [str(exc)]

        for idx, chunk in enumerate(reader):
            try:
                chunks.append(chunk)
            except Exception as exc:  # pragma: no cover - per-chunk errors
                msg = f"Chunk {idx} failed: {exc}"
                logger.error(msg)
                errors.append(msg)

        try:
            df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
        except Exception as exc:  # pragma: no cover - concat errors
            logger.error("Failed concatenating chunks: %s", exc)
            errors.append(str(exc))
            df = pd.DataFrame()
        return df, errors


__all__ = ["StreamProcessor"]
