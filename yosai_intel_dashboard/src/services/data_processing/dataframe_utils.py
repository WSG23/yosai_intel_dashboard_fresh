"""Shared DataFrame parsing utilities."""

from __future__ import annotations

import io
import json
import logging
from typing import Optional, Tuple

import pandas as pd

from yosai_intel_dashboard.src.infrastructure.config.constants import DEFAULT_CHUNK_SIZE
from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import dynamic_config
from core.performance import get_performance_monitor
from yosai_intel_dashboard.src.core.interfaces.protocols import ConfigurationProtocol
from yosai_intel_dashboard.src.utils.file_utils import safe_decode_with_unicode_handling

logger = logging.getLogger(__name__)


def process_dataframe(
    decoded: bytes,
    filename: str,
    *,
    config: ConfigurationProtocol = dynamic_config,
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Parse ``decoded`` bytes into a DataFrame based on ``filename`` extension."""
    try:
        filename_lower = filename.lower()
        monitor = get_performance_monitor()
        chunk_size = getattr(config.analytics, "chunk_size", DEFAULT_CHUNK_SIZE)

        if filename_lower.endswith(".csv"):
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    text = safe_decode_with_unicode_handling(decoded, encoding)
                    reader = pd.read_csv(
                        io.StringIO(text),
                        on_bad_lines="skip",
                        encoding="utf-8",
                        low_memory=False,
                        dtype=str,
                        keep_default_na=False,
                        chunksize=chunk_size,
                    )
                    chunks = []
                    for chunk in reader:
                        monitor.throttle_if_needed()
                        chunks.append(chunk)
                    df = (
                        pd.concat(chunks, ignore_index=True)
                        if chunks
                        else pd.DataFrame()
                    )
                    return df, None
                except UnicodeDecodeError:
                    continue
            return None, "Could not decode CSV with any standard encoding"
        elif filename_lower.endswith(".json"):
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    text = safe_decode_with_unicode_handling(decoded, encoding)
                    reader = pd.read_json(
                        io.StringIO(text),
                        lines=True,
                        chunksize=chunk_size,
                    )
                    chunks = []
                    for chunk in reader:
                        monitor.throttle_if_needed()
                        chunks.append(chunk)
                    df = (
                        pd.concat(chunks, ignore_index=True)
                        if chunks
                        else pd.DataFrame()
                    )
                    return df, None
                except UnicodeDecodeError:
                    continue
            return None, "Could not decode JSON with any standard encoding"
        elif filename_lower.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(decoded))
            return df, None
        else:
            return None, f"Unsupported file type: {filename}"
    except (
        UnicodeDecodeError,
        ValueError,
        pd.errors.ParserError,
        json.JSONDecodeError,
    ) as e:
        return None, f"Error processing file: {str(e)}"
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected error processing file", exc_info=exc)
        raise
